#!/usr/bin/env ruby

filename = ARGV[0]
filename_base = File.basename(filename)

`convert #{filename} -thumbnail '200x135>' -unsharp 0x.5 #{filename_base}_thumb.jpg`
`convert #{filename} -thumbnail '200x135^' -unsharp 0x.5 -gravity center -extent '200x135' #{filename_base}_center_thumb.jpg`
`convert #{filename} -resize '670x400^' -gravity center -extent '670x400' #{filename_base}_middle.jpg`
`convert #{filename} -resize '670x400^' -gravity South -extent '670x400' #{filename_base}_bottom.jpg`
`convert #{filename} -resize '670x400^' -gravity North -extent '670x400' #{filename_base}_top.jpg`
`convert #{filename} -resize '670x400^' -size 670x400 -gravity center -crop 670x400 #{filename_base}_crop.jpg`
