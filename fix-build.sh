#!/bin/bash
echo "Locating and patching headers in bin/chimera..."

# 1. Patch main.hpp files
find bin/chimera -name "main.hpp" | while read -r header; do
    if ! grep -q "Wignored-attributes" "$header"; then
        echo "Patching $header"
        sed -i '1i #pragma GCC diagnostic ignored "-Wignored-attributes"' "$header"
    else
        echo "$header already patched."
    fi
done

# 2. Initialize dependency trackers
echo "Initializing dependency trackers in bin/chimera..."
mkdir -p bin/chimera/.deps/exports
for lib in conn ctrl shared memory special memstore extern third-party swarm-kv fusee chimera; do
    touch "bin/chimera/.deps/exports/${lib}.conanbuild"
done

# 3. Patch the Conan Profile for your system's GCC version
PROFILE_PATH="bin/chimera/conan/profiles/gcc-12-relwithdebinfo.profile"
if [ -f "$PROFILE_PATH" ]; then
    # Detect actual GCC version (e.g., 13)
    ACTUAL_GCC_VERSION=$(gcc -dumpversion | cut -d. -f1)
    echo "Detected GCC version $ACTUAL_GCC_VERSION. Patching profile..."
    
    # Update the profile to match your system version
    sed -i "s/compiler.version=[0-9]*/compiler.version=$ACTUAL_GCC_VERSION/g" "$PROFILE_PATH"
    
    # Ensure Conan's settings.yml knows about this version
    conan profile update settings.compiler.version=$ACTUAL_GCC_VERSION default 2>/dev/null
else
    echo "Warning: Profile not found at $PROFILE_PATH"
fi

echo "Patching experiment scripts for cluster library paths..."
find experiments/ -name "*.sh" | while read -r script; do
    if ! grep -q "LD_LIBRARY_PATH" "$script"; then
        # Inject the library path export at the second line of every script
        sed -i "2i export LD_LIBRARY_PATH=\"$BASE_DIR/bin/chimera/.deps/gcc/relwithdebinfo/lib:\$LD_LIBRARY_PATH\"" "$script"
    fi
done

echo "Done. You can now build using the artifact script."