#!/bin/sh -e

# Generate some chessboard JPGs for testing with.

dir=test
[ -d $dir ] || mkdir $dir

convert -size 100x100 pattern:gray50 -scale 1600% -sampling-factor 2x2 \
    -crop 796x396+0+0 $dir/chess-2x2.jpg
convert -size 100x100 pattern:gray50 -scale 800%x1600% -sampling-factor 1x2 \
    -crop 796x396+0+0 $dir/chess-1x2.jpg
convert -size 100x100 pattern:gray50 -scale 1600%x800% -sampling-factor 2x1 \
    -crop 796x396+0+0 $dir/chess-2x1.jpg
convert -size 100x100 pattern:gray50 -scale 800% -sampling-factor 1x1 \
    -crop 796x396+0+0 $dir/chess-1x1.jpg
