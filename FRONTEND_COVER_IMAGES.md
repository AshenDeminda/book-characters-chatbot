# Cover Images for Frontend

## Book Covers Location

Cover images have been moved to the frontend. Place them in your frontend's public/assets folder.

## Available Cover Images

The following cover images are available in `static/covers/` (to be moved to frontend):

1. **Harry Potter.png** - For `harry_potter_1` book
2. **Narnia.png** - For `chronicles_narnia` book  
3. **The Hobbits.png** - For `the_hobbit` book

## Frontend Implementation

### Option 1: Store in Frontend Public Folder
```
frontend/
  public/
    assets/
      covers/
        harry-potter.png
        narnia.png
        the-hobbit.png
```

### Option 2: Use book_id to Map Images
```typescript
const coverImages: Record<string, string> = {
  'harry_potter_1': '/assets/covers/harry-potter.png',
  'chronicles_narnia': '/assets/covers/narnia.png',
  'the_hobbit': '/assets/covers/the-hobbit.png'
};

// In your component:
<img src={coverImages[book.book_id]} alt={book.title} />
```

### Option 3: Use External CDN
You can also host these images on a CDN like Cloudinary, AWS S3, or Imgur.

## API Changes

The `cover_image` field in the API response is now `null`:
```json
{
  "book_id": "harry_potter_1",
  "cover_image": null,  // Frontend handles the image
  "title": "Harry Potter and the Philosopher's Stone"
}
```

## Migration Steps

1. Copy the 3 PNG files from `backend/static/covers/` to your frontend assets folder
2. Update your frontend code to use local images based on `book_id`
3. The backend no longer serves static files
