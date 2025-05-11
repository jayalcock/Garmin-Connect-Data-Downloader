# Backup Location Changes

## Changes Made

1. **Renamed function from `copy_to_icloud` to `backup_data_file`**
   - Updated function name to be more generic and not tied to a specific cloud provider
   - Enhanced clarity by focusing on what the function does rather than where it copies to

2. **Changed backup destination from iCloud to Nextcloud**
   - Updated the backup path from `~/Library/Mobile Documents/com~apple~CloudDocs/Garmin Health Data` to `/Users/jay/Nextcloud/Garmin Health Data`
   - Ensures more reliable backup operations as iCloud was having issues

3. **Updated output messages to reflect new backup location**
   - Changed "Copied file to iCloud" to "Backed up file to Nextcloud"
   - Updated "Created backup in iCloud" to "Created dated backup in Nextcloud"

4. **Updated all references in the codebase**
   - Updated function calls in the main `get_stats` function
   - Fixed test references in `test_downloader.py` and `test_data_retrieval.py`
   - Updated parameter names in tests from `mock_copy` to `mock_backup`

5. **Updated documentation to reflect the changes**
   - Modified README.md to mention Nextcloud instead of iCloud
   - Updated CHANGELOG.md to reflect the backup location change
   - Updated menu text in the interactive interface

## Benefits of This Change

1. **More reliable backup storage** - Nextcloud offers better control over backups
2. **Clearer function naming** - Function name now reflects its purpose, not its destination
3. **Consistent terminology** - "backup" instead of "copy" throughout the codebase

## Remaining Issues

Some tests are still failing due to mock issues with authentication, but these are unrelated to the backup location changes and can be addressed separately if needed. The core backup functionality is working as expected.
