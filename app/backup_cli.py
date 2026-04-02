import click
from app.backup import (
    export_to_json, export_to_sql, import_from_json, import_from_sql, _get_backups_list
)


@click.group()
def backup():
    """Database backup and restore commands."""
    pass


@backup.command()
@click.option('--output', '-o', help='Custom output path for backup file')
def export_json(output):
    """Export all records to JSON format."""
    try:
        path = export_to_json(output)
        click.echo(click.style(f'✓ Backup created: {path}', fg='green'))
    except Exception as e:
        click.echo(click.style(f'✗ Error: {str(e)}', fg='red'))


@backup.command()
@click.option('--output', '-o', help='Custom output path for backup file')
def export_sql(output):
    """Export database to SQL dump format."""
    try:
        path = export_to_sql(output)
        click.echo(click.style(f'✓ Backup created: {path}', fg='green'))
    except Exception as e:
        click.echo(click.style(f'✗ Error: {str(e)}', fg='red'))


@backup.command()
@click.option('--output', '-o', help='Custom output directory for backup files')
def export_all(output):
    """Export both JSON and SQL backups."""
    try:
        if output:
            import os
            os.makedirs(output, exist_ok=True)
            json_path = export_to_json(os.path.join(output, 'backup.json'))
            sql_path = export_to_sql(os.path.join(output, 'backup.sql'))
        else:
            json_path = export_to_json()
            sql_path = export_to_sql()

        click.echo(click.style('✓ Backups created:', fg='green'))
        click.echo(f'  JSON: {json_path}')
        click.echo(f'  SQL:  {sql_path}')
    except Exception as e:
        click.echo(click.style(f'✗ Error: {str(e)}', fg='red'))


@backup.command()
@click.argument('file_path')
def import_json(file_path):
    """Import records from JSON backup file."""
    try:
        success, message, count = import_from_json(file_path)
        if success:
            click.echo(click.style(f'✓ {message}', fg='green'))
        else:
            click.echo(click.style(f'✗ {message}', fg='red'))
    except Exception as e:
        click.echo(click.style(f'✗ Error: {str(e)}', fg='red'))


@backup.command()
@click.argument('file_path')
def import_sql(file_path):
    """Import database from SQL dump file."""
    try:
        success, message = import_from_sql(file_path)
        if success:
            click.echo(click.style(f'✓ {message}', fg='green'))
        else:
            click.echo(click.style(f'✗ {message}', fg='red'))
    except Exception as e:
        click.echo(click.style(f'✗ Error: {str(e)}', fg='red'))


@backup.command()
def list():
    """List existing backup files."""
    backups = _get_backups_list()
    if not backups:
        click.echo('No backups found.')
        return

    click.echo(click.style('Existing backups:', fg='cyan'))
    for backup in backups:
        size_mb = backup['size'] / (1024 * 1024)
        click.echo(f"  {backup['name']} - {size_mb:.2f} MB - {backup['created'].strftime('%Y-%m-%d %H:%M:%S')}")
