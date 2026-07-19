import json
import os
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

RETENTION_DAYS = 30
DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive.file']


class Command(BaseCommand):
    help = (
        'Dumps the database with pg_dump and uploads it to a Google Drive backup folder, '
        'pruning uploads older than RETENTION_DAYS. This is disaster-recovery insurance, '
        'not a fix for the database being temporarily paused/unreachable.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-upload',
            action='store_true',
            help='Run pg_dump only and leave the file in place, for local testing without Drive credentials.',
        )

    def handle(self, *args, **options):
        db = settings.DATABASES['default']
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H%M%S')
        filename = f'nandy_inventory_backup_{timestamp}.dump'

        if options['skip_upload']:
            dump_path = os.path.join(tempfile.gettempdir(), filename)
            self._run_pg_dump(db, dump_path)
            self.stdout.write(self.style.SUCCESS(f'Dump written to {dump_path} (upload skipped).'))
            return

        folder_id = os.environ.get('BACKUP_DRIVE_FOLDER_ID')
        credentials_json = os.environ.get('BACKUP_GOOGLE_CREDENTIALS_JSON')
        if not folder_id or not credentials_json:
            raise CommandError(
                'BACKUP_DRIVE_FOLDER_ID and BACKUP_GOOGLE_CREDENTIALS_JSON must be set '
                '(or pass --skip-upload for a local dry run).'
            )

        with tempfile.TemporaryDirectory() as tmp_dir:
            dump_path = os.path.join(tmp_dir, filename)
            self._run_pg_dump(db, dump_path)

            drive = self._get_drive_client(credentials_json)
            self._upload(drive, folder_id, dump_path, filename)
            pruned = self._prune_old_backups(drive, folder_id)

        self.stdout.write(self.style.SUCCESS(
            f'Backup {filename} uploaded to Drive. Pruned {pruned} backup(s) older than {RETENTION_DAYS} days.'
        ))

    def _run_pg_dump(self, db, dump_path):
        env = os.environ.copy()
        env['PGPASSWORD'] = db['PASSWORD']
        cmd = [
            'pg_dump',
            '-Fc',  # custom format: compressed, restorable with pg_restore, supports selective restore
            '-h', db['HOST'],
            '-p', str(db.get('PORT') or 5432),
            '-U', db['USER'],
            '-d', db['NAME'],
            '-f', dump_path,
        ]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            raise CommandError(f'pg_dump failed: {result.stderr}')

    def _get_drive_client(self, credentials_json):
        # Imported lazily so `--skip-upload` works without the google-api packages
        # ever needing to touch network/auth machinery.
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        info = json.loads(credentials_json)
        credentials = service_account.Credentials.from_service_account_info(info, scopes=DRIVE_SCOPES)
        return build('drive', 'v3', credentials=credentials)

    def _upload(self, drive, folder_id, dump_path, filename):
        from googleapiclient.http import MediaFileUpload

        file_metadata = {'name': filename, 'parents': [folder_id]}
        media = MediaFileUpload(dump_path, mimetype='application/octet-stream', resumable=False)
        drive.files().create(body=file_metadata, media_body=media, fields='id').execute()

    def _prune_old_backups(self, drive, folder_id):
        cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
        query = f"'{folder_id}' in parents and trashed = false"
        results = drive.files().list(q=query, fields='files(id, name, createdTime)').execute()

        pruned = 0
        for f in results.get('files', []):
            created = datetime.strptime(f['createdTime'], '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
            if created < cutoff:
                drive.files().delete(fileId=f['id']).execute()
                pruned += 1
        return pruned
