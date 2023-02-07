#ifndef UTIL_H
#define UTIL_H

#include <stdio.h>

#define fail() printf("File \"%s\", line %d, in %s\n", __FILE__, __LINE__, __func__)
#define bool_fail() fail();return false
#define null_fail() fail();return NULL

#endif /* ~UTIL_H */
