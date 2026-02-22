"""
Guard migration: detects databases that are stuck in the partial-migration state
where 0001_initial was applied as BigAutoField (bigint) but 0002 failed before
it could run the AlterField. In that state the model expects a UUID primary key
but the database column is still bigint.

For a fresh PostgreSQL installation (or any DB that fully applied 0001 + 0002
originally) the id column is already uuid and this migration is a no-op.

If the check fails, run:
    python manage.py migrate stc_analysis zero
    python manage.py migrate stc_analysis
to rebuild the table from scratch (safe when the table has no data to preserve).
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stc_analysis', '0002_stcanalysis_branch_analyzed_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name  = 'stc_analysis_stcanalysis'
                          AND column_name = 'id'
                          AND data_type   = 'bigint'
                    ) THEN
                        RAISE EXCEPTION
                            'STCAnalysis.id is still bigint – the UUID migration '
                            'was never applied. Fix with: '
                            'python manage.py migrate stc_analysis zero '
                            '&& python manage.py migrate stc_analysis';
                    END IF;
                END $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
            hints={'target_db': 'postgresql'},
        ),
    ]
