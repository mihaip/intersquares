# Intersections + Foursquare = Intersquares

My entry ([and a finalist](http://blog.foursquare.com/2011/09/28/announcing-the-global-hackathon-winners/)) in the [2011 Foursquare Global Hackathon](https://github.com/foursquare/hackathon/wiki/Foursquare-Global-Hackathon). Based on an idea that I had while having dinner with [Ann](http://twitter.com/annparparita) and [Dan](http://twitter.com/dbentley) at [Sprout](https://foursquare.com/v/sprout-cafe/49e6233bf964a5200f641fe3):

> The premise of the show [How I Met Your Mother](http://en.wikipedia.org/wiki/How_I_Met_Your_Mother) is that in the year 2030 the narrator (Ted) is telling his kids how he met their mother. He starts the story 25 years earlier (i.e. in 2005), and thus far (after 6 years), we've gotten a lot of hints, but we haven't met the mother yet. However, it's quite apparent that Ted has in fact been at the same venue as the mother several times. In a hypothetical world where Ted and the mother use Foursquare, I thought it would be neat if they could compare checkin  histories and see all the near-misses that they had over the years.

Intersquares does exactly that: you can sign in with your Foursquare account, and then once your checkin history is processed, another user can sign in with their account, and you'll both be told where you were together (whether you knew it at the time or not). This can be great for [remembering first dates](https://twitter.com/herGreekness/status/115834434015608832) or for [finding close calls](https://twitter.com/bobthecow/status/115837047222177793).

Deployed live at [intersquares.com](http://www.intersquares.com/). You can also watch [a screencast of how it works](http://www.youtube.com/watch?v=0oHPOzuRqD8).

## Configuration

Copy `app/base/foursquare_config.py.template` to `app/base/foursquare_config.py` and replace the placeholders with your OAuth client ID and secret (obtained when you [register your app with Foursquare](https://foursquare.com/developers/register)).

## Scripts (located in `scripts/`)

- `run.sh`: Runs `app/` with the App Engine dev server on port 8083
- `deploy.sh`: Deploys `app/` to prod App Engine
