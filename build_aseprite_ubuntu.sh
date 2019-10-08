if [[ "$OSTYPE" == "linux-gnu" ]]; then
        # Ubuntu / Linux

        # Download dependencies such as cmake, ninja and some librarys
        sudo apt-get install -y g++ cmake ninja-build libx11-dev libxcursor-dev libgl1-mesa-dev libfontconfig1-dev

        # Clone the aseprite repo
        git clone --recursive https://github.com/aseprite/aseprite.git
        aseprite_path=$(pwd)

        # Create $HOME/deps forler, clones depot_tools and skia into it and builds skia
        mkdir $HOME/deps
        cd $HOME/deps
        git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
        git clone -b aseprite-m71 https://github.com/aseprite/skia.git
        export PATH="${PWD}/depot_tools:${PATH}"
        cd skia
        python tools/git-sync-deps
        gn gen out/Release --args="is_official_build=true skia_use_system_expat=false skia_use_system_icu=false skia_use_libjpeg_turbo=false skia_use_system_libpng=false skia_use_system_libwebp=false skia_use_system_zlib=false extra_cflags_cc=[\"-frtti\"]"
        ninja -C out/Release skia

        # Move back into aseprite folder, config cmake file and build
        cd $aseprite_path
        cd aseprite
        mkdir build
        cd build
        cmake \
          -DCMAKE_BUILD_TYPE=RelWithDebInfo \
          -DLAF_OS_BACKEND=skia \
          -DSKIA_DIR=$HOME/deps/skia \
          -DSKIA_OUT_DIR=$HOME/deps/skia/out/Release \
          -G Ninja \
          ..
        ninja aseprite
elif [[ "$OSTYPE" == "darwin"* ]]; then
        # Mac OSX
        brew install cmake ninja 
else
        echo 'Error! Unsupported OS...'
fi