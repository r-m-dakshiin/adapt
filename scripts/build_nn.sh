#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
mkdir -p native

cat > native/nn.c <<'C'
#include <math.h>
/* Simple logistic scorer; swap for your real C NN. */
float score_conversion(float* features, int n) {
    float w[5] = {0.9f, -0.6f, 1.1f, 0.4f, -0.3f};
    float z = 0.0f;
    for (int i = 0; i < n && i < 5; i++) z += features[i] * w[i];
    return 1.0f / (1.0f + expf(-z));
}
C

cc -shared -fPIC -O2 native/nn.c -o native/libnn.so -lm
echo "Built native/libnn.so"
