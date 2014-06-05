#!/usr/bin/env ruby

filename = ARGV[0]
filename_base = File.basename(filename)

`convert #{filename} -thumbnail '200x135>' -unsharp 0x.5 #{filename_base}_thumb.jpg`
`convert #{filename} -thumbnail '200x135^' -unsharp 0x.5 -gravity center -extent '200x135' #{filename_base}_center_thumb.jpg`
`convert #{filename} -resize '800x480^' -gravity center -extent '800x480' #{filename_base}_middle.jpg`
`convert #{filename} -resize '800x480^' -gravity South -extent '800x480' #{filename_base}_bottom.jpg`
`convert #{filename} -resize '800x480^' -gravity North -extent '800x480' #{filename_base}_top.jpg`
`convert #{filename} -resize '800x480^' -size 800x480 -gravity center -crop 800x480 #{filename_base}_crop.jpg`
