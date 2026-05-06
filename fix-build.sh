#!/bin/bash
# Fix for GCC 13+ Attribute errors
echo "Patching headers for GCC 13 compatibility..."
sed -i '1i #pragma GCC diagnostic ignored "-Wignored-attributes"' bin/swarm-kv/swarm-kv/src/main.hpp
sed -i '1i #pragma GCC diagnostic ignored "-Wignored-attributes"' bin/swarm-kv/chimera/src/main.hpp
sed -i '1i #pragma GCC diagnostic ignored "-Wignored-attributes"' bin/swarm-kv/fusee/src/main.hpp

# Fix for missing .deps trackers
echo "Initializing dependency trackers..."
mkdir -p bin/swarm-kv/.deps/exports
for lib in conn ctrl shared memory special memstore extern third-party swarm-kv fusee chimera; do
    touch "bin/swarm-kv/.deps/exports/${lib}.conanbuild"
done

echo "Done. You can now run: ./bin/swarm-kv/build.sh swarm-kv fusee"
