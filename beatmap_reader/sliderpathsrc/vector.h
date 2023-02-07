#ifndef VECTOR_H
#define VECTOR_H

#include "stdbool.h"

typedef struct {
    double x, y;
} Vector2;

static Vector2 *vector2_init(double x, double y);
static double vector2_magnitude(Vector2 *v);
static bool vector2_equal(Vector2 *v1, Vector2 *v2);
static void vector2_normalize(Vector2 *v);
static double vector2_dot(Vector2 *v1, Vector2 *v2);

#endif /* ~VECTOR_H */