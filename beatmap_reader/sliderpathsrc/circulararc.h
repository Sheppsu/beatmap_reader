#ifndef CIRCULARARC_H
#define CIRCULARARC_H

#include <stdlib.h>
#include <stdbool.h>
#include "vector.h"
#include "list.h"

typedef struct {
    bool isValid;
    double thetaStart;
    double thetaRange;
    double direction;
    float radius;
    Vector2 *center;
} CircularArcProperties;

extern CircularArcProperties *carcprop_init(EfficientList *vPoints);
extern void carcprop_free(CircularArcProperties *carc);

#endif /* ~CIRCULARARC_H */