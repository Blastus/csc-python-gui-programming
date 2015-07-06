#include <stdint.h>

typedef int8_t SByte;
typedef int16_t Int16;
typedef int32_t Int32;
typedef int64_t Int64;

typedef uint8_t Byte;
typedef uint16_t UInt16;
typedef uint32_t UInt32;
typedef uint64_t UInt64;

/*
 * http://hg.python.org/releasing/3.2.3/file/86d1421a552c/Include/object.h
 */

typedef struct {
    Int64 ob_refcnt;
    TypeP ob_type;
} Object, *ObjectP;

typedef struct {
    Object ob_base;
    Int64 ob_size;
} VarObj, *VarObjP;

#define refcnt(ob) (((ObjectP)(ob))->ob_refcnt)
#define type(ob)   (((ObjectP)(ob))->ob_type)
#define size(ob)   (((VarObjP)(ob))->ob_size)

typedef struct {
    
} Type, *TypeP;