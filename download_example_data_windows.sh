Invoke-WebRequest -Uri 'http://cseweb.ucsd.edu/~viscomp/projects/LF/papers/ECCV20/nerf/tiny_nerf_data.npz' -OutFile './tiny_nerf_data.npz' 
mkdir -p data
cd data
Invoke-WebRequest -Uri http://cseweb.ucsd.edu/~viscomp/projects/LF/papers/ECCV20/nerf/nerf_example_data.zip -OutFile './nerf_example_data.zip'
unzip nerf_example_data.zip
cd ..
