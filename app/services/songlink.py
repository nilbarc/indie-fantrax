import httpx
from urllib.parse import quote


async def get_songlink_data(url: str) -> dict:
    """
    Fetch data from Songlink/Odesli API.
    Returns Spotify URL, Apple Music URL, album metadata, and Songlink URL.
    """
    encoded_url = quote(url, safe="")
    api_url = f"https://api.song.link/v1-alpha.1/links?url={encoded_url}"

    async with httpx.AsyncClient() as client:
        response = await client.get(api_url, timeout=30.0)
        response.raise_for_status()
        data = response.json()

    result = {
        "spotify_url": None,
        "apple_music_url": None,
        "songlink_url": data.get("pageUrl"),
        "album_title": None,
        "artist_name": None,
        "album_art_url": None,
    }

    # Extract platform links
    links_by_platform = data.get("linksByPlatform", {})

    if "spotify" in links_by_platform:
        result["spotify_url"] = links_by_platform["spotify"].get("url")

    if "appleMusic" in links_by_platform:
        result["apple_music_url"] = links_by_platform["appleMusic"].get("url")

    # Extract metadata from entities
    entities = data.get("entitiesByUniqueId", {})
    if entities:
        # Get the first entity for metadata
        first_entity = next(iter(entities.values()), {})
        result["album_title"] = first_entity.get("title")
        result["artist_name"] = first_entity.get("artistName")
        result["album_art_url"] = first_entity.get("thumbnailUrl")

    return result
