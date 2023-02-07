#ifndef LIST_H
#define LIST_H

#include <stdbool.h>

typedef struct {
    void *value;
    size_t size;
} ListValue;

typedef struct {
    ListValue **values;
    size_t length;
} List;

static List *list_init();
static ListValue *list_create_value(void *value, size_t valueSize);
static bool list_append(List *l, void *value, size_t valueSize);
static bool list_insert(List *l, void *value, size_t valueSize, size_t index);
static void *list_get(List *l, size_t index);
static bool list_set(List *l, size_t index, void *value, size_t valueSize);
static bool list_remove(List *l, size_t index);
static void *list_pop(List *l, size_t index, size_t *sizeBuf);
static void list_free(List *l);


typedef struct {
    void *values;
    size_t length;
    size_t itemSize;
} EfficientList;

static EfficientList *efflist_init(size_t length, size_t valueSize);
static void efflist_free(EfficientList *list);
static bool efflist_checkerr(EfficientList *list, size_t index);
static void *efflist_get(EfficientList *list, size_t index);
static bool efflist_set(EfficientList *list, size_t index, void * value);
static bool efflist_contains_address(EfficientList *list, void *ptr);

#endif /* ~LIST_H */