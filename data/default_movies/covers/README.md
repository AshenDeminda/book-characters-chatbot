# Movie Covers

This directory is for movie cover images (handled by frontend).

The backend API returns `cover_image: null` in the response. Frontend should map `movie_id` to local image files.

## Required Images

Place these images in your frontend assets folder:

1. `the_shawshank_redemption.jpg` - The Shawshank Redemption (1994)
2. `the_godfather.jpg` - The Godfather (1972)
3. `inception.jpg` - Inception (2010)

## Frontend Mapping

```javascript
const movieCovers = {
  'the_shawshank_redemption': '/assets/covers/movies/the_shawshank_redemption.jpg',
  'the_godfather': '/assets/covers/movies/the_godfather.jpg',
  'inception': '/assets/covers/movies/inception.jpg'
};
```
