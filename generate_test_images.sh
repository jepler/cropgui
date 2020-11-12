#!/bin/sh -e

# Generate some chessboard JPGs for testing with.

dir=test
[ -d $dir ] || mkdir $dir

text='-density 72 -pointsize 32 -weight Bold -gravity NorthWest -fill rgba(255,0,0,0.5) -annotate +0+0 A -annotate +32+32 B -annotate +64+64 C -annotate +96+96 D -annotate +128+128 E -annotate +160+160 F -annotate +192+192 G -annotate +224+224 H -annotate +256+256 I -annotate +288+288 J -annotate +320+320 K -fill rgba(0,255,0,0.5) -annotate +352+352 L -annotate +384+320 M -annotate +416+288 N -annotate +448+256 O -annotate +480+224 P -annotate +512+192 Q -annotate +544+160 R -annotate +576+128 S -annotate +608+96 T -annotate +640+64 U -annotate +672+32 V -fill rgba(0,0,255,0.5) -annotate +704+0 W -annotate +736+32 X -annotate +768+64 Y'
convert -size 100x100 pattern:gray50 -scale 1600% -sampling-factor 2x2 \
    -crop 796x396+0+0 $text $dir/chess-2x2.jpg
convert -size 100x100 pattern:gray50 -scale 800%x1600% -sampling-factor 1x2 \
    -crop 796x396+0+0 $text $dir/chess-1x2.jpg
convert -size 100x100 pattern:gray50 -scale 1600%x800% -sampling-factor 2x1 \
    -crop 796x396+0+0 $text $dir/chess-2x1.jpg
convert -size 100x100 pattern:gray50 -scale 800% -sampling-factor 1x1 \
    -crop 796x396+0+0 $text $dir/chess-1x1.jpg
