#include "vector.h"
#include "util.h"
#include "math.h"


static Vector2 *vector2_init(double x, double y) {
    Vector2 *v = malloc(sizeof(Vector2));
    if (v == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Failed to create a Vector2 object due to malloc failing");
        null_fail();
    }
    v->x = x;
    v->y = y;
    return v;
}


static double vector2_magnitude(Vector2 *v) {
    return sqrt(pow(v->x, 2) + pow(v->y, 2));
}


static bool vector2_equal(Vector2 *v1, Vector2 *v2) {
    return v1->x == v2->x && v1->y == v2->y;
}

static void vector2_normalize(Vector2 *v) {
    double magnitude = vector2_magnitude(v);
    v->x /= magnitude;
    v->y /= magnitude;
}

static double vector2_dot(Vector2 *v1, Vector2 *v2) {
    return v1->x * v2->x + v1->y * v2->y;
}
