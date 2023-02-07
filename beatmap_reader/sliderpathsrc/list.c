#include "list.h"
#include "util.h"
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>


static List* list_init() {
    List* l = malloc(sizeof(List));
    if (l == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Failed to create List object due to malloc failing");
        null_fail();
    }
    l->length = 0;
    return l;
}

static ListValue* list_create_value(void *value, size_t valueSize) {
    ListValue* listValue = malloc(sizeof(ListValue));
    if (listValue == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Failed to create ListValue object due to malloc failing");
        null_fail();
    }
    listValue->value = malloc(valueSize);
    if (listValue->value == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate memory for ListValue.value due to malloc failing");
        null_fail();
    }
    if (memcpy_s(listValue->value, valueSize, value, valueSize) != 0) {
        PyErr_SetString(PyExc_MemoryError, "Failed to initialize ListValue.value due to memcpy_s failing");
        null_fail();
    }
    listValue->size = valueSize;
    return listValue;
}

bool _list_increment_size(List *l) {
    l->length++;
    ListValue **newPointer = realloc(l->values, l->length*sizeof(ListValue*));
    if (newPointer == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Failed to increment list size due to realloc failing");
        bool_fail();
    }
    l->values = newPointer;
    return true;
}

bool _list_decrement_size(List *l) {
    l->length--;
    if (l->length == 0) {
        free(l->values);
        l->values = NULL;
        return true;
    }
    ListValue **newPointer = realloc(l->values, l->length*sizeof(ListValue*));
    if (newPointer == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Failed to decrement list size due to realloc failing");
        bool_fail();
    }
    l->values = newPointer;
    return true;
}

bool _list_init_values(List *l) {
    l->length++;
    l->values = malloc(sizeof(ListValue*));
    if (l->values == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Failed to init list values due to malloc failing");
        bool_fail();
    }
    return true;
}

static bool list_append(List *l, void *value, size_t valueSize) {
    bool success = l->length == 0 ? _list_init_values(l) : _list_increment_size(l);
    if (!success) {bool_fail();}
    ListValue *lValue = list_create_value(value, valueSize);
    if (lValue == NULL) {bool_fail();}
    l->values[l->length-1] = lValue;
    return true;
}

static bool list_insert(List *l, void *value, size_t valueSize, size_t index) {
    if (l->length == 0) {return list_append(l, value, valueSize);}
    if (!_list_increment_size(l)) {bool_fail();}
    for (size_t i=l->length-1; i>index; i--) {l->values[i] = l->values[i-1];}
    ListValue *lValue = list_create_value(value, valueSize);
    if (lValue == NULL) {bool_fail();}
    l->values[index] = lValue;
    return true;
}

bool _list_remove(List *l, size_t index) {
    free(l->values[index]);
    if (l->length>1) {
        for (size_t i=index; i<l->length-1; i++) {
            if (memcpy_s(&l->values[i], sizeof(ListValue*), &l->values[i+1], sizeof(ListValue*)) != 0) {
                PyErr_SetString(PyExc_MemoryError, 
                "Failed to move pointer down 1 index in memory due to memcpy_s failing");
                bool_fail();
            }
        }
    }
    if (!_list_decrement_size(l)) {bool_fail();}
    return true;
}

bool list_checkerr(List *l, size_t index) {
    if (index < 0 || index >= l->length) {
        char error[200];
        sprintf(error, "Attempted to performed index-specific operation on list with \
            length %zd and index %zd", l->length, index);
        PyErr_SetString(PyExc_ValueError, error);
        bool_fail();
    }
    return true;
}

static void *list_get(List *l, size_t index) {
    if (!list_checkerr(l, index)) {null_fail();}
    return l->values[index]->value;
}

static bool list_set(List *l, size_t index, void *value, size_t valueSize) {
    if (!list_checkerr(l, index)) {bool_fail();}
    list_remove(l, index);
    list_insert(l, value, valueSize, index);
    return true;
}

static bool list_remove(List *l, size_t index) {
    if (!list_checkerr(l, index)) {bool_fail();}
    free(l->values[index]->value);
    if (!_list_remove(l, index)) {bool_fail();}
    return true;
}

static void* list_pop(List *l, size_t index, size_t *sizeBuf) {
    if (!list_checkerr(l, index)) {null_fail();}
    if (sizeBuf != NULL) {*sizeBuf = l->values[index]->size;}
    void *value = l->values[index]->value;
    if (!_list_remove(l, index)) {null_fail();}
    return value;
}

static void list_free(List *l) {
    for (size_t i=0; i<l->length; i++) {
        free(l->values[i]->value);
        free(l->values[i]);
    }
    free(l->values);
    free(l);
}


static EfficientList *efflist_init(size_t length, size_t valueSize) {
    EfficientList *list = malloc(sizeof(EfficientList));
    if (list == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Failed to create an EfficientList object due to malloc failing");
        null_fail();
    }
    list->length = length;
    list->itemSize = valueSize;
    list->values = calloc(length, valueSize);
    if (list->values == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Failed to create an EfficientList object due to calloc failing");
        null_fail();
    }
    return list;
}

static void efflist_free(EfficientList *list) {
    free(list->values);
    free(list);
}

static bool efflist_checkerr(EfficientList *list, size_t index) {
    if (index < 0 || index >= list->length) {
        char error[200];
        sprintf(error, "Attempted to performed index-specific operation on efficient list with \
            length %zd and index %zd", list->length, index);
        PyErr_SetString(PyExc_ValueError, error);
        bool_fail();
    }
    return true;
}

static void *efflist_get(EfficientList *list, size_t index) {
    if (!efflist_checkerr(list, index)) {null_fail();}
    void *ptr = list->values;
    ptr = (char*)ptr + list->itemSize*index;
    return ptr;
}

static bool efflist_set(EfficientList *list, size_t index, void * value) {
    if (!efflist_checkerr(list, index)) {bool_fail();}
    void *ptr = list->values;
    ptr = (char*)ptr + list->itemSize*index;
    if (memcpy_s(ptr, list->itemSize, value, list->itemSize) != 0) {bool_fail();}
    return true;
}

static bool efflist_contains_address(EfficientList *list, void *ptr) {
    return (ptr >= list->values && (char*)ptr < (char*)list->values + list->length*list->itemSize);
}
