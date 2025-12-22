# Catalog Setup - Google Drive Link Approach

## Database Setup

You need to create a `catalog_settings` table in your Supabase database. Run this SQL in your Supabase SQL Editor:

```sql
-- Create catalog_settings table
CREATE TABLE IF NOT EXISTS catalog_settings (
  id SERIAL PRIMARY KEY,
  google_drive_link TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create a function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to auto-update updated_at
CREATE TRIGGER update_catalog_settings_updated_at 
  BEFORE UPDATE ON catalog_settings
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Insert initial record (optional)
INSERT INTO catalog_settings (google_drive_link)
VALUES ('')
ON CONFLICT DO NOTHING;
```

## Setting the Google Drive Link

### Option 1: Via API (Recommended)

Use the admin API endpoint:

```bash
PUT /api/catalog/link
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "google_drive_link": "https://drive.google.com/file/d/YOUR_FILE_ID/view?usp=sharing"
}
```

### Option 2: Directly in Supabase

1. Go to your Supabase dashboard
2. Navigate to Table Editor
3. Open `catalog_settings` table
4. Insert or update the `google_drive_link` field with your Google Drive link

## Google Drive Link Formats

The API accepts various Google Drive link formats:
- `https://drive.google.com/file/d/FILE_ID/view?usp=sharing`
- `https://drive.google.com/open?id=FILE_ID`
- `https://drive.google.com/uc?id=FILE_ID`

The API will automatically convert them to direct download links.

## Benefits of This Approach

✅ No large PDF files in repository  
✅ Easy to update - just change the link  
✅ No redeployment needed when catalog changes  
✅ Can be updated via API or database  
✅ Works perfectly in serverless environments  

## API Endpoints

- `GET /api/catalog/download` - Downloads catalog (redirects to Google Drive if link is set)
- `GET /api/catalog/info` - Returns catalog information
- `GET /api/catalog/link` - Get current catalog link (admin only)
- `PUT /api/catalog/link` - Update catalog link (admin only)
- `POST /api/catalog/upload` - Upload PDF file (fallback, not recommended for production)

