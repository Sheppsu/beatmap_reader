#include "circulararc.h"
#include "Python.h"
#include "vector.h"
#include "util.h"
#include "constants.h"
#define _USE_MATH_DEFINES
#include <math.h>


extern CircularArcProperties *carcprop_init(EfficientList *vPoints) {
    CircularArcProperties *carc = malloc(sizeof(CircularArcProperties));
    if (carc == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Failed to create CircularArcProperties object due to malloc failing");
		null_fail();
    }

    Vector2 *a = efflist_get(vPoints, 0);
    Vector2 *b = efflist_get(vPoints, 1);
    Vector2 *c = efflist_get(vPoints, 2);
    if (a == NULL || b == NULL || c == NULL) {null_fail();}

    if (fabs((b->y - a->y) * (c->x - a->x) - (b->x - a->x) * (c->y - a->y)) <= (double)DOUBLE_EPSILON) {
        carc->isValid = false;
        return carc;
    }


    double d = 2 * (a->x * (b->y - c->y) + b->x * (c->y - a->y) + c->x * (a->y - b->y));
    double aSq = pow(vector2_magnitude(a), 2);
    double bSq = pow(vector2_magnitude(b), 2);
    double cSq = pow(vector2_magnitude(c), 2);

    Vector2 *center = vector2_init(
        (aSq * (b->y - c->y) + bSq * (c->y - a->y) + cSq * (a->y - b->y)) / d,
        (aSq * (c->x - b->x) + bSq * (a->x - c->x) + cSq * (b->x - a->x)) / d
    );
    if (center == NULL) {null_fail();}
    carc->center = center;

    Vector2 *dA = vector2_init(
        a->x - center->x,
        a->y - center->y
    );
    Vector2 *dC = vector2_init(
        c->x - center->x,
        c->y - center->y
    );
    if (dA == NULL || dC == NULL) {null_fail();}
    
    carc->radius = (float)vector2_magnitude(dA);
    carc->thetaStart = atan2(dA->y, dA->x);
    double thetaEnd = atan2(dC->y, dC->x);
    while (thetaEnd < carc->thetaStart)  thetaEnd += 2 * M_PI;

    carc->direction = 1;
    carc->thetaRange = thetaEnd - carc->thetaStart;

    Vector2 *orthoAtoC = vector2_init(
        c->y - a->y,
        -(c->x - a->x)
    );
    if (orthoAtoC == NULL) {null_fail();}
    Vector2 *bMinusA = vector2_init(
        b->x - a->x,
        b->y - a->y
    );

    if (vector2_dot(orthoAtoC, bMinusA) < 0) {
        carc->direction = -carc->direction;
        carc->thetaRange = 2 * M_PI - carc->thetaRange;
    }

    carc->isValid = true;

    free(dA);
    free(dC);
    free(orthoAtoC);
    free(bMinusA);
    return carc;
}

extern void carcprop_free(CircularArcProperties *carc) {
    free(carc->center);
    free(carc);
}
