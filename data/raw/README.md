# Raw Data Directory

This directory contains raw music data files uploaded for processing.

## Supported File Formats
- CSV files (*.csv)
- Excel files (*.xlsx, *.xls)  
- TSV files (*.tsv)

## Organization
Organize files by platform for easier processing:
- `spotify/` - Spotify streaming data
- `apple/` - Apple Music data
- `youtube/` - YouTube Music data
- `amazon/` - Amazon Music data

## File Naming Convention
Use descriptive names that include:
- Platform name
- Data type (streaming, sales, etc.)
- Date range
- Example: `spotify_streaming_2024_Q1.csv`

## Security Note
Raw data files are ignored by git for security and size reasons.
Never commit sensitive music industry data to version control.
