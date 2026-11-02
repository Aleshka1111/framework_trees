python3 graph_generator.py erg -n 10 -p 0.5 -minw 1 -maxw 10 -o output/erg.json
python3 graph_generator.py planar -n 20 -w 100 -h 100 -p1 0.3 -p2 0.4 -o output/planar.json
python3 prim.py output/erg.json
python3 prim.py output/planar.json
python3 kraskal.py output/erg.json
python3 kraskal.py output/planar.json