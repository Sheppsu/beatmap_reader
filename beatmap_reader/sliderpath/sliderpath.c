#define PY_SSIZE_T_CLEAN
#include "Python.h"
#include "vector.c"
#include "list.c"
#include "circulararc.c"
#include "constants.h"
#include "util.h"
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>


// debug helping functions

void print_vector(Vector2 *v) {
    printf("<%g, %g>", v->x, v->y);
}

void print_efflist(EfficientList *list) {
    printf("[");
    for (size_t i=0; i<list->length; i++) {
        Vector2 *v = efflist_get(list, i);
        if (v == NULL) {printf("OOPS!\n");}
        print_vector(v);
        if (i != list->length-1) printf(", ");
    }
    printf("]");
}

void print_list(List *list) {
    printf("[");
    for (size_t i=0; i<list->length; i++) {
        print_efflist(list->values[i]->value);
        if (i != list->length-1) printf(", ");
    }
    printf("]");
}


// input output helping functions

EfficientList *parse_points(PyObject *points) {
    EfficientList *vPoints = efflist_init(PyList_Size(points), sizeof(Vector2));
    if (vPoints == NULL) {null_fail();}
    for (size_t i=0; i<vPoints->length; i++) {
        PyObject *point = PyList_GetItem(points, i);
        Vector2 *v = vector2_init(
            PyFloat_AsDouble(PyTuple_GetItem(point, 0)),
            PyFloat_AsDouble(PyTuple_GetItem(point, 1))
        );
        if (v == NULL) {null_fail();}
        if (!efflist_set(vPoints, i, v)) {null_fail();}
    }

    return vPoints;
}

List *parse_points_list(PyObject *points) {
    List *vPoints = list_init();
    if (vPoints == NULL) {null_fail();}
    size_t vPointsSize = PyList_Size(points);
    for (size_t i=0; i<vPointsSize; i++) {
        PyObject *point = PyList_GetItem(points, i);
        Vector2 *v = vector2_init(
            PyFloat_AsDouble(PyTuple_GetItem(point, 0)),
            PyFloat_AsDouble(PyTuple_GetItem(point, 1))
        );
        if (v == NULL) {null_fail();}
        if (!list_append(vPoints, v, sizeof(Vector2))) {null_fail();}
    }

    return vPoints;
}

EfficientList *parse_args(PyObject *args) {
    PyObject *rawPoints;

    if (!PyArg_ParseTuple(args, "O:approximate_bezier", &rawPoints)) {
        null_fail();
    }

    return parse_points(rawPoints);
}

PyObject *vector2_list_to_pylist(List *list) {
    PyObject *pyOutput = PyList_New(list->length);
    for (size_t i=0; i<list->length; i++) {
        Vector2 *point = list->values[i]->value;
        PyList_SetItem(pyOutput, i, PyTuple_Pack(2, PyFloat_FromDouble(point->x), 
            PyFloat_FromDouble(point->y)));
    }
    return pyOutput;
}


// bezier functions

char bezier_is_flat_enough(EfficientList *points) {
    for (size_t i=1; i<points->length-1; i++) {
        Vector2 *point1 = efflist_get(points, i-1);
        Vector2 *point2 = efflist_get(points, i);
        Vector2 *point3 = efflist_get(points, i+1);
        if (point1 == NULL || point2 == NULL || point3 == NULL) {fail();return 2;}
        Vector2 *calcPoint = vector2_init(point1->x-2*point2->x+point3->x, point1->y-2*point2->y+point3->y);
        if (calcPoint == NULL) {fail();return 2;}
        if (pow(vector2_magnitude(calcPoint), 2) > BEZIER_TOLERANCE * BEZIER_TOLERANCE * 4) {
            return 0;
        }
        free(calcPoint);
    }
    return 1;
}

bool bezier_subdivide(EfficientList *points, EfficientList *l, EfficientList *r, 
EfficientList *subdivisionBuffer, size_t count) {
    size_t bufLength = subdivisionBuffer->length;
    EfficientList *midPoints = efflist_init(bufLength, sizeof(Vector2));
    if (midPoints == NULL) {bool_fail();} 

    for (size_t i=0; i<max(bufLength, count); i++) {
        Vector2 *v = efflist_get(i<count ? points : subdivisionBuffer, i);
        if (v == NULL) {bool_fail();}
        if (!efflist_set(midPoints, i, v)) {bool_fail();}
    }

    for (size_t i=0; i<count; i++) {
        Vector2 *v1 = efflist_get(midPoints, 0);
        Vector2 *v2 = efflist_get(midPoints, count-i-1);
        if (v1 == NULL || v2 == NULL) {bool_fail();}
        if (!efflist_set(l, i, v1)) {bool_fail();}
        if (!efflist_set(r, count-i-1, v2)) {bool_fail();}

        for (size_t j=0; j<count-i-1; j++) {
            Vector2 *v1 = efflist_get(midPoints, j);
            Vector2 *v2 = efflist_get(midPoints, j+1);
            if (v1 == NULL || v2 == NULL) {bool_fail();}
            v1->x = (v1->x+v2->x)/2;
            v1->y = (v1->y+v2->y)/2;
        }
    }

    efflist_free(midPoints);
    return true;
}

bool bezier_approximate(EfficientList *points, List *output, EfficientList *subdivisionBuffer1, 
EfficientList *subdivisionBuffer2, size_t count) {
    EfficientList *l = efflist_init(subdivisionBuffer2->length, sizeof(Vector2));
    EfficientList *r = efflist_init(subdivisionBuffer1->length, sizeof(Vector2));
    if (l == NULL || r == NULL) {bool_fail();}
    size_t bufSize1 = sizeof(Vector2)*subdivisionBuffer1->length;
    size_t bufSize2 = sizeof(Vector2)*subdivisionBuffer2->length;
    errno_t s1 = memcpy_s(l->values, bufSize2, subdivisionBuffer2->values, bufSize2);
    errno_t s2 = memcpy_s(r->values, bufSize1, subdivisionBuffer1->values, bufSize1);
    if (s1 != 0 || s2 != 0) {
        PyErr_SetString(PyExc_MemoryError, "Failed to copy values to l->values and/or r->values due to memcpy_s failing");
        bool_fail();
    }
    
    if (!bezier_subdivide(points, l, r, subdivisionBuffer1, count)) {bool_fail();}

    for (size_t i=0; i<count-1; ++i) {
        Vector2 *v = efflist_get(r, i+1);
        if (v == NULL) {bool_fail();}
        if (!efflist_set(l, count+i, v)) {bool_fail();}
    }

    Vector2 *firstPoint = efflist_get(points, 0);
    if (firstPoint == NULL) {bool_fail();}
    Vector2 *copy = vector2_init(firstPoint->x, firstPoint->y);
    if (copy == NULL) {bool_fail();}
    if (!list_append(output, copy, sizeof *copy)) {bool_fail();}

    for (size_t i=1; i<count-1; ++i) {
        size_t index = 2 * i;
        Vector2 *p1 = efflist_get(l, index-1);
        Vector2 *p2 = efflist_get(l, index);
        Vector2 *p3 = efflist_get(l, index+1);
        if (p1 == NULL || p2 == NULL || p3 == NULL) {bool_fail();}
        Vector2 *p = vector2_init(
            0.25f * (p1->x + 2 * p2->x + p3->x),
            0.25f * (p1->y + 2 * p2->y + p3->y)
        );
        if (p == NULL) {bool_fail();}
        if (!list_append(output, p, sizeof *p)) {bool_fail();}
    }

    efflist_free(l);
    efflist_free(r);
    return true;
}

static PyObject *sliderpath_approximate_bezier(PyObject *self, PyObject *args) {
    EfficientList *vPoints = parse_args(args);
    if (vPoints == NULL) {null_fail();}
    size_t nPoints = vPoints->length;

    if (nPoints <= 1) {
        PyErr_SetString(PyExc_ValueError, "The list given to bezier calculate has 1 or less points");
        null_fail();
    }

    List *output = list_init();
    if (output == NULL) {null_fail();}

    List *toFlatten = list_init();
    if (toFlatten == NULL) {null_fail();}
    if (!list_insert(toFlatten, vPoints, sizeof *vPoints, 0)) {null_fail();}
    List *freeBuffers = list_init();
    if (freeBuffers == NULL) {null_fail();}

    EfficientList *subdivisionBuffer1 = efflist_init(nPoints, sizeof(Vector2));
    EfficientList *subdivisionBuffer2 = efflist_init(nPoints * 2 - 1, sizeof(Vector2));
    EfficientList *leftChild = efflist_init(subdivisionBuffer2->length, sizeof(Vector2));
    if (subdivisionBuffer1 == NULL || subdivisionBuffer2 == NULL || leftChild == NULL) {null_fail();}

    while (toFlatten->length > 0) {
        EfficientList *parent = list_pop(toFlatten, 0, NULL);
        if (parent == NULL) {null_fail();}

        char isFlat = bezier_is_flat_enough(parent);
        if (isFlat == 2) {null_fail();}
        if (isFlat) {
            if (!bezier_approximate(parent, output, subdivisionBuffer1, subdivisionBuffer2, 
                nPoints)) {null_fail();}

            if (!list_insert(freeBuffers, parent, sizeof *parent, 0)) {null_fail();}
            continue;
        }

        EfficientList *rightChild = freeBuffers->length > 0 ? 
            list_pop(freeBuffers, 0, NULL) : 
            efflist_init(nPoints, sizeof(Vector2));
        if (rightChild == NULL) {null_fail();}
        
        if (!bezier_subdivide(parent, leftChild, rightChild, subdivisionBuffer1, 
            nPoints)) {null_fail();}

        for (size_t i=0; i<nPoints; ++i) {
            Vector2 *v = efflist_get(leftChild, i);
            if (v == NULL) {null_fail();}
            if (!efflist_set(parent, i, v)) {null_fail();}
        }

        if (!list_insert(toFlatten, rightChild, sizeof *rightChild, 0)) {null_fail();}
        if (!list_insert(toFlatten, parent, sizeof *parent, 0)) {null_fail();}
    }
    
    Vector2 *lastPoint = efflist_get(vPoints, nPoints-1);
    if (lastPoint == NULL || !list_append(output, lastPoint, sizeof *lastPoint)) {null_fail();}
    PyObject *pyOutput = vector2_list_to_pylist(output);

    // TODO: make sure this frees up all values to avoid memory leak
    list_free(output);
    efflist_free(vPoints);
    efflist_free(subdivisionBuffer1);
    efflist_free(subdivisionBuffer2);
    efflist_free(leftChild);
    free(toFlatten);
    free(freeBuffers);
    return pyOutput;
}


// catmull functions

double catmull_calc_point(double n1, double n2, double n3, double n4, double t, double t2, double t3) {
    return 0.5f * (2.0f * n2 + (-n1 + n3) * t + (2.0f * n1 - 5.0f * n2 + 4.0f * n3 - n4) * t2 + (-n1 + 3.0f * n2 - 3.0f * n3 + n4) * t3);
}

Vector2 *catmull_find_point(Vector2 *v1, Vector2 *v2, Vector2 *v3, Vector2 *v4, double t) {
    double t2 = t * t;
    double t3 = t * t2;

    Vector2 *result = vector2_init(
        catmull_calc_point(v1->x, v2->x, v3->x, v4->x, t, t2, t3),
        catmull_calc_point(v1->y, v2->y, v3->y, v4->y, t, t2, t3)
    );
    if (result == NULL) {null_fail();}
    return result;
}

static PyObject *sliderpath_approximate_catmull(PyObject *self, PyObject *args) {
    EfficientList *vPoints = parse_args(args);
    if (vPoints == NULL) {null_fail();} 
    if (vPoints->length <= 1) {
        PyErr_SetString(PyExc_ValueError, "The list given to bezier calculate has 1 or less points");
        null_fail();
    }

    List *result = list_init();
    if (result == NULL) {null_fail();}

    for (size_t i=0; i<vPoints->length-1; i++) {
        Vector2 *v1 = efflist_get(vPoints, i > 0 ? (i-1) : i);
        Vector2 *v2 = efflist_get(vPoints, i);
        if (v1 == NULL || v2 == NULL) {null_fail();}
        Vector2 *v3 = i < vPoints->length - 1 ? 
            efflist_get(vPoints, i + 1) : 
            vector2_init(v2->x * 2 - v1->x, v2->y * 2 - v1->y);
        if (v3 == NULL) {null_fail();}
        Vector2 *v4 = i < vPoints->length - 2 ? 
            efflist_get(vPoints, i + 2) : 
            vector2_init(v3->x * 2 - v2->x, v3->y * 2 - v2->y);
        if (v4 == NULL) {null_fail();}

        for (int c = 0; c < CATMULL_DETAIL; c++) {
            Vector2 *p1 = catmull_find_point(v1, v2, v3, v4, (double)c / CATMULL_DETAIL);
            Vector2 *p2 = catmull_find_point(v1, v2, v3, v4, (double)(c+1) / CATMULL_DETAIL);
            if (p1 == NULL || p2 == NULL) {null_fail();}
            if (!list_append(result, p1, sizeof *p1)) {null_fail();}
            if (!list_append(result, p2, sizeof *p2)) {null_fail();}
            free(p1);
            free(p2);
        }
        if (!efflist_contains_address(vPoints, v3)) free(v3);
        if (!efflist_contains_address(vPoints, v4)) free(v4);
    }

    PyObject *output = vector2_list_to_pylist(result);
    efflist_free(vPoints);
    list_free(result);
    return output;
}


static PyObject *sliderpath_approximate_circular_arc(PyObject *self, PyObject *args) {
    EfficientList *vPoints = parse_args(args);
    if (vPoints == NULL) {null_fail();}
    if (vPoints->length <= 1) {
        PyErr_SetString(PyExc_ValueError, "The list given to bezier calculate has 1 or less points");
        null_fail();
    }

    CircularArcProperties *pr = carcprop_init(vPoints);
    if (pr == NULL) {null_fail();}
    
    if (!pr->isValid) {
        efflist_free(vPoints);
        return sliderpath_approximate_bezier(self, args);
    }

    size_t nPoints = 2 * pr->radius <= CIRCULAR_ARC_TOLERANCE ? 2 : \
        max(2, (int)ceil(pr->thetaRange / (2 * acos(1 - CIRCULAR_ARC_TOLERANCE / pr->radius))));

    List *output = list_init();
    if (output == NULL) {null_fail();}

    for (size_t i=0; i<nPoints; ++i) {
        double fract = (double)i / (nPoints - 1);
        double theta = pr->thetaStart + pr->direction * fract * pr->thetaRange;
        Vector2 *o = vector2_init(
            cos(theta) * pr->radius + pr->center->x,
            sin(theta) * pr->radius + pr->center->y
        );
        if (o == NULL) {null_fail();}
        if (!list_append(output, o, sizeof *o)) {null_fail();}
        free(o);
    }

    PyObject *pyOutput = vector2_list_to_pylist(output);
    efflist_free(vPoints);
    carcprop_free(pr);
    list_free(output);
    return pyOutput;
}


// other slider path calculation functions

static PyObject *sliderpath_calculate_length(PyObject *self, PyObject *args) {
    PyObject *rawPoints;
    PyObject *rawPath;
    PyObject *pySegmentEnds;
    double expectedDistance;

    if (!PyArg_ParseTuple(args, "OOOd:calculate_length", &rawPoints, &rawPath, &pySegmentEnds, 
        &expectedDistance)) {
        null_fail();
    }

    List *path = parse_points_list(rawPath);
    EfficientList *points = parse_points(rawPoints);
    EfficientList *segmentEnds = efflist_init(PyList_Size(pySegmentEnds), sizeof(double));
    if (path == NULL || points == NULL || segmentEnds == NULL) {null_fail();}
    for (size_t i=0; i<segmentEnds->length; i++) {
        double num = PyFloat_AsDouble(PyList_GetItem(pySegmentEnds, i));
        if (!efflist_set(segmentEnds, i, &num)) {null_fail();}
    }

    double calculatedLength = 0;
    List *cumulativeLength = list_init();
    if (cumulativeLength == NULL) {null_fail();}
    if (!list_append(cumulativeLength, &calculatedLength, sizeof calculatedLength)) {null_fail();}

    for (size_t i=0; i<path->length-1; i++) {
        Vector2 *p1 = list_get(path, i+1);
        Vector2 *p2 = list_get(path, i);
        Vector2 *diff = vector2_init(p1->x - p2->x, p1->y - p2->y);
        if (diff == NULL) {null_fail();}
        calculatedLength += vector2_magnitude(diff);
        if (!list_append(cumulativeLength, &calculatedLength, sizeof calculatedLength)) {null_fail();}
        free(diff);
    }

    if (expectedDistance != calculatedLength) {
        if (points->length >= 2 && expectedDistance > calculatedLength) {
            Vector2 *lastPoint = efflist_get(points, points->length-1);
            Vector2 *secondLastPoint = efflist_get(points, points->length-2);
            if (lastPoint == NULL || secondLastPoint == NULL) {null_fail();}
            if (vector2_equal(lastPoint, secondLastPoint)) {
                list_append(cumulativeLength, &calculatedLength, sizeof calculatedLength);
                goto return_values;
            }
        }

        if (!list_remove(cumulativeLength, cumulativeLength->length-1)) {null_fail();}

        size_t pathEndIndex = path->length - 1;

        if (calculatedLength > expectedDistance) {
            double *lastLength = list_get(cumulativeLength, cumulativeLength->length-1);
            if (lastLength == NULL) {null_fail();}
            while (cumulativeLength->length > 0 && *lastLength >= expectedDistance) {
                if (!list_remove(cumulativeLength, cumulativeLength->length-1)) {null_fail();}
                if (!list_remove(path, pathEndIndex--)) {null_fail();}

                if (segmentEnds->length > 0) {
                    double *num = efflist_get(segmentEnds, segmentEnds->length-1);
                    if (num == NULL) {null_fail();}
                    *num--;
                }

                lastLength = list_get(cumulativeLength, cumulativeLength->length-1);
                if (lastLength == NULL) {null_fail();}
            }
        }

        if (pathEndIndex <= 0) {
            double zero = 0;
            if (!list_append(cumulativeLength, &zero, sizeof zero)) {null_fail();}
            goto return_values;
        }

        Vector2 *v1 = list_get(path, pathEndIndex);
        Vector2 *v2 = list_get(path, pathEndIndex-1);
        if (v1 == NULL || v2 == NULL) {null_fail();}
        Vector2 *dir = vector2_init(v1->x - v2->x, v1->y - v2->y);
        if (dir == NULL) {null_fail();}
        vector2_normalize(dir);

        double *lastLength = list_get(cumulativeLength, cumulativeLength->length-1);
        if (lastLength == NULL) {null_fail();}
        dir->x *= (double)(expectedDistance - *lastLength);
        dir->x += v2->x;
        dir->y *= (double)(expectedDistance - *lastLength);
        dir->y += v2->y;

        if (!list_set(path, pathEndIndex, dir, sizeof *dir)) {null_fail();}
        if (!list_append(cumulativeLength, &expectedDistance, sizeof expectedDistance)) {null_fail();}
    }

return_values:

    PyObject *output = PyList_New(3);
    PyObject *newPath = PyList_New(path->length);
    PyObject *newSegmentEnds = PyList_New(segmentEnds->length);
    PyObject *newCumulativeLength = PyList_New(cumulativeLength->length);
    size_t maxLength = max(max(path->length, segmentEnds->length), cumulativeLength->length); 
    for (size_t i=0; i<maxLength; i++) {
        if (i<path->length) {
            Vector2 *point = list_get(path, i);
            if (point == NULL) {null_fail();}
            PyList_SetItem(newPath, i, PyTuple_Pack(2, PyFloat_FromDouble(point->x), 
                PyFloat_FromDouble(point->y)));
        }
        if (i<segmentEnds->length) {
            double *num = efflist_get(segmentEnds, i);
            if (num == NULL) {null_fail();}
            PyList_SetItem(newSegmentEnds, i, PyFloat_FromDouble(*num));
        }
        if (i<cumulativeLength->length) {
            double *num = list_get(cumulativeLength, i);
            if (num == NULL) {null_fail();}
            PyList_SetItem(newCumulativeLength, i, PyFloat_FromDouble(*num));
        }
    }
    PyList_SetItem(output, 0, newPath);
    PyList_SetItem(output, 1, newSegmentEnds);
    PyList_SetItem(output, 2, newCumulativeLength);
    return output;
}


// module stuff

static PyMethodDef sliderpath_methods[] = {
    {"approximate_bezier", sliderpath_approximate_bezier, METH_VARARGS},
    {"approximate_catmull", sliderpath_approximate_catmull, METH_VARARGS},
    {"approximate_circular_arc", sliderpath_approximate_circular_arc, METH_VARARGS},
    {"calculate_length", sliderpath_calculate_length, METH_VARARGS},
    {NULL, NULL}
};

static struct PyModuleDef sliderpathmodule = {
    PyModuleDef_HEAD_INIT,
    "sliderpath",
    "slider path approximation",
    0,
    sliderpath_methods,
};

PyMODINIT_FUNC PyInit_sliderpath(void) {
    return PyModuleDef_Init(&sliderpathmodule);
}
