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

extern List* list_init();
extern ListValue* list_create_value(void *value, size_t valueSize);
extern bool list_append(List *l, void *value, size_t valueSize);
extern bool list_insert(List *l, void *value, size_t valueSize, size_t index);
extern void* list_get(List *l, size_t index);
extern bool list_set(List *l, size_t index, void *value, size_t valueSize);
extern bool list_remove(List *l, size_t index);
extern void* list_pop(List *l, size_t index, size_t *sizeBuf);
extern void list_free(List *l);


typedef struct {
    void *values;
    size_t length;
    size_t itemSize;
} EfficientList;

extern EfficientList *efflist_init(size_t length, size_t valueSize);
extern void efflist_free(EfficientList *list);
extern bool efflist_checkerr(EfficientList *list, size_t index);
extern void* efflist_get(EfficientList *list, size_t index);
extern bool efflist_set(EfficientList *list, size_t index, void * value);
extern bool efflist_contains_address(EfficientList *list, void *ptr);

#endif /* ~LIST_H */