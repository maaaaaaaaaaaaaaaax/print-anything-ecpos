# migrations

Numbered SQL files are applied in order by the migration runner in `storage`. The first one, `0001_initial.sql`, creates the text-job table and its status-order index. Settings, assets, and paper storage remain future migrations.
