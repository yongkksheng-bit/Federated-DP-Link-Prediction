# P5FC Acquisition Transport Note

The first post-freeze acquisition invocation downloaded the Flickr adjacency
but its standard-library connection ended before transferring the 340 MiB
feature file. No source manifest or matrix statistic was produced. The
allowlist, Google Drive IDs, datasets, protocol, and gates remain unchanged.

The acquisition helper was changed to use resumable `curl` transfer when
available, retaining the same frozen URL and writing through a `.partial`
file. This is an operational transport correction made before source parsing,
split generation, or result access; it does not modify the scientific design.
