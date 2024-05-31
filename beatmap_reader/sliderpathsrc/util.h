#ifndef UTIL_H
#define UTIL_H

#include <stdio.h>

// file offset set by builder
#define __FILE_OFFSET__ 0
#define __FILE_NAME__ (__FILE__ + __FILE_OFFSET__)
#define fail() printf("File \"%s\", line %d, in %s\n", __FILE_NAME__, __LINE__, __func__)
#define bool_fail() fail();return false
#define null_fail() fail();return NULL

#endif /* ~UTIL_H */
