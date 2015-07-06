/* Provide an implementation of Markov Encryption for simplified use.
 * 
 * This module exposes primitives useful for executing Markov Encryption
 * processes. ME was inspired by a combination of Markov chains with the
 * puzzles of Sudoku. This implementation has undergone numerous changes
 * and optimizations since its original design. Please see documentation.
 * 
 * Author:  Stephen "Zero" Chappell <Noctis.Skytower@gmail.com>
 * Date:    1 September 2012
 * Version: 0.9.0
 */

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef unsigned char byte;
typedef unsigned short word;
typedef unsigned long dword;
typedef signed char sbyte;
typedef signed short sword;
typedef signed long sdword;

typedef struct {
    sdword references;
} object;

#define CLASS                                                                   \
typedef struct {                                                                \
    object metadata;

CLASS
    dword size;
    byte *data;
} bytes;

CLASS
    bytes *data;
    dword offset;
} iter_bytes;

CLASS
    sdword start;
    sdword stop;
    sdword step;
} range;

CLASS
    range *data;
    sword finish;
    sword offset;
} iter_range;

CLASS
    bool member[256];
} set;

CLASS
    set *data;
    word offset;
} iter_set;

CLASS
    set *keys;
    byte values[256];
} dict;

CLASS
    dict *data;
    iter_set *iter;
} iter_dict;

CLASS
    dword size;
    void **data;
} list;

CLASS
    list *data;
    dword offset;
} iter_list;

CLASS
    bytes *buffer;
    dword offset;
} deque;

CLASS
    deque *data;
    dword offset;
} iter_deque;

CLASS
    list *data;
    word prefix_len;
    bytes *base;
    word size;
    bytes *encoder;
    list *axes;
    bytes *order;
    list *decoder;
} Key;

CLASS
    bytes *data;
} Primer;

CLASS
    Key *primary;
    dict *encoder;
    deque *prefix;
    bytes *decoder;
} _Processor;

typedef _Processor Encrypter;
typedef _Processor Decrypter;

void _raise(char *file, int line, char *type, char *text);
#define raise(type, text) _raise(__FILE__, __LINE__, type, text)

#define assert(condition, text)                                                 \
    if (!(condition))                                                           \
        raise("Assertion", text)

#define assert_iter(type) assert(iter_##type##_valid(self), "iter_" #type " could not retrieve value!")
        
#define assert_not_null(var) assert(var != NULL, #var " should not be null!")

#define assert_self() assert_not_null(self)

static dword memory_new_count = 0;
static dword memory_del_count = 0;

#define new(type, var, count)                                                   \
    var = (type *)malloc(count * sizeof(type));                                 \
    assert(var != NULL, "(" #type ")" #var " could not be allocated!");         \
    memory_new_count += 1

#define del(var)                                                                \
    free(var);                                                                  \
    memory_del_count += 1

#define resize(type, var, count)                                                \
    var = (type *)realloc(var, (count) * sizeof(type));                         \
    assert(var != NULL, "(" #type ")" #var " could not be reallocated!")

#define zero(type, var, count) memset(var, 0, (count) * sizeof(type))

#define object_call(type, ...)                                                  \
    type *self;                                                                 \
    self = type##_new();                                                        \
    type##_init(self, ##__VA_ARGS__);                                           \
    return self

static dword object_new_count = 0;
static dword object_del_count = 0;

#define object_new(type)                                                        \
    type *self;                                                                 \
    new(type, self, 1);                                                         \
    self->metadata.references = 1;                                              \
    object_new_count += 1;                                                      \
    return self

#define object_copy(type)                                                       \
    if (self != NULL)                                                           \
        self->metadata.references += 1;                                         \
    return self

#define object_del(type)                                                        \
    do                                                                          \
    {                                                                           \
        if (self != NULL)                                                       \
        {                                                                       \
            assert(self->metadata.references > 0, "Object does not exist!");    \
            self->metadata.references -= 1;                                     \
            if (self->metadata.references < 1)                                  \
            {                                                                   \
                do { } while (false)

#define end_object_del()                                                        \
                object_del_count += 1;                                          \
                del(self);                                                     \
            }                                                                   \
        }                                                                       \
    }                                                                           \
    while (false)

#define iter_current(item, container_type) iter_##container_type##_current(item##_iterator)
#define iter_key(item, container_type) iter_##container_type##_key(item##_iterator)
#define iter_next(item, container_type) iter_##container_type##_next(item##_iterator)
#define iter_rewind(item, container_type) iter_##container_type##_rewind(item##_iterator)
#define iter_stop(item, container_type) iter_##container_type##_stop(item##_iterator)
#define iter_valid(item, container_type) iter_##container_type##_valid(item##_iterator)

#define foreach(item_type, item, container_type, container)                     \
    do                                                                          \
    {                                                                           \
        iter_##container_type *item##_iterator;                                 \
        item_type item;                                                         \
        for (item##_iterator = container_type##_iter(container); iter_valid(item, container_type); iter_next(item, container_type)) \
        {                                                                       \
            item = iter_current(item, container_type)

#define end_foreach(item, container_type)                                       \
        }                                                                       \
        iter_##container_type##_del(item##_iterator);                           \
    }                                                                           \
    while (false)

bytes *bytes_from_string(char *string);
bytes *bytes_from_buffer(dword size, byte *buffer);
bytes *bytes_from_set(set *group);
bytes *bytes_call(dword size);
bytes *bytes_new(void);
bytes *bytes_copy(bytes *self);
void bytes_del(bytes *self);
void bytes_init(bytes *self, dword size);
#define bytes_iter(self) iter_bytes_call(self)
char *bytes_hex(bytes *self);
char *bytes_repr(bytes *self);
bool bytes_bool(bytes *self);
dword bytes_len(bytes *self);
bytes *bytes_deepcopy(bytes *self);
byte bytes_getitem(bytes *self, dword offset);
void bytes_setitem(bytes *self, dword offset, byte value);
bool bytes_find(bytes *self, byte value, dword *offset);
dword bytes_index(bytes *self, byte value);
void bytes_sort(bytes *self);
void bytes_rotate(bytes *self, dword offset);
sbyte bytes_cmp(bytes *self, bytes *other);
bool bytes_lt(bytes *self, bytes *other);
bool bytes_le(bytes *self, bytes *other);
bool bytes_eq(bytes *self, bytes *other);
bool bytes_ne(bytes *self, bytes *other);
bool bytes_gt(bytes *self, bytes *other);
bool bytes_ge(bytes *self, bytes *other);

int byte_cmp(const void *a, const void *b);

iter_bytes *iter_bytes_call(bytes *data);
iter_bytes *iter_bytes_new(void);
iter_bytes *iter_bytes_copy(iter_bytes *self);
void iter_bytes_del(iter_bytes *self);
void iter_bytes_init(iter_bytes *self, bytes *data);
byte iter_bytes_current(iter_bytes *self);
dword iter_bytes_key(iter_bytes *self);
void iter_bytes_next(iter_bytes *self);
void iter_bytes_rewind(iter_bytes *self);
void iter_bytes_stop(iter_bytes *self);
bool iter_bytes_valid(iter_bytes *self);

range *range_stop(sdword stop);
range *range_start_stop(sdword start, sdword stop);
range *range_call(sdword start, sdword stop, sdword step);
range *range_new(void);
range *range_copy(range *self);
void range_del(range *self);
void range_init(range *self, sdword start, sdword stop, sdword step);
#define range_iter(self) iter_range_call(self)

iter_range *iter_range_call(range *data);
iter_range *iter_range_new(void);
iter_range *iter_range_copy(iter_range *self);
void iter_range_del(iter_range *self);
void iter_range_init(iter_range *self, range *data);
sdword iter_range_current(iter_range *self);
sdword iter_range_key(iter_range *self);
void iter_range_next(iter_range *self);
void iter_range_rewind(iter_range *self);
void iter_range_stop(iter_range *self);
bool iter_range_valid(iter_range *self);

set *set_from_bytes(bytes *data);
set *set_call(void);
set *set_new(void);
set *set_copy(set *self);
void set_del(set *self);
void set_init(set *self);
#define set_iter(self) iter_set_call(self)
bool set_bool(set *self);
word set_len(set *self);
bool set_contains(set *self, byte elem);
bool set_issubset(set *self, set *other);
bool set_issuperset(set *self, set *other);
set *set_union(set *self, set *other);
set *set_intersection(set *self, set *other);
set *set_difference(set *self, set *other);
set *set_symmetric_difference(set *self, set *other);
set *set_deepcopy(set *self);
void set_add(set *self, byte elem);
void set_remove(set *self, byte elem);
void set_discard(set *self, byte elem);
void set_clear(set *self);
set *set_mutate(set *self, set *other, bool add);

iter_set *iter_set_call(set *data);
iter_set *iter_set_new(void);
iter_set *iter_set_copy(iter_set *self);
void iter_set_del(iter_set *self);
void iter_set_init(iter_set *self, set *data);
bool iter_set_current(iter_set *self);
word iter_set_key(iter_set *self);
void iter_set_next(iter_set *self);
void iter_set_rewind(iter_set *self);
void iter_set_stop(iter_set *self);
bool iter_set_valid(iter_set *self);
byte iter_set_current_member(iter_set *self);
void iter_set_next_member(iter_set *self);
void iter_set_rewind_member(iter_set *self);

dict *dict_from_pairs(bytes *keys, bytes *values);
dict *dict_call(void);
dict *dict_new(void);
dict *dict_copy(dict *self);
void dict_del(dict *self);
void dict_init(dict *self);
#define dict_iter(self) iter_dict_call(self)
bool dict_bool(dict *self);
word dict_len(dict *self);
bool dict_contains(dict *self, byte key);
byte dict_getitem(dict *self, byte key);
void dict_setitem(dict *self, byte key, byte value);
void dict_delitem(dict *self, byte key);
bytes *dict_keys(dict *self);
bytes *dict_values(dict *self);
dict *dict_reversed(dict *self);

iter_dict *iter_dict_call(dict *data);
iter_dict *iter_dict_new(void);
iter_dict *iter_dict_copy(iter_dict *self);
void iter_dict_del(iter_dict *self);
void iter_dict_init(iter_dict *self, dict *data);
byte iter_dict_current(iter_dict *self);
byte iter_dict_key(iter_dict *self);
void iter_dict_next(iter_dict *self);
void iter_dict_rewind(iter_dict *self);
void iter_dict_stop(iter_dict *self);
bool iter_dict_valid(iter_dict *self);

list *list_call(dword size);
list *list_new(void);
list *list_copy(list *self);
void list_del(list *self);
void list_init(list *self, dword size);
#define list_iter(self) iter_list_call(self)
bool list_bool(list *self);
dword list_len(list *self);
void *list_getitem(list *self, dword offset);
void list_setitem(list *self, dword offset, void *value);

iter_list *iter_list_call(list *data);
iter_list *iter_list_new(void);
iter_list *iter_list_copy(iter_list *self);
void iter_list_del(iter_list *self);
void iter_list_init(iter_list *self, list *data);
void *iter_list_current(iter_list *self);
dword iter_list_key(iter_list *self);
void iter_list_next(iter_list *self);
void iter_list_rewind(iter_list *self);
void iter_list_stop(iter_list *self);
bool iter_list_valid(iter_list *self);

deque *deque_call(bytes *buffer);
deque *deque_new(void);
deque *deque_copy(deque *self);
void deque_del(deque *self);
void deque_init(deque *self, bytes *buffer);
#define deque_iter(self) iter_deque_call(self)
bool deque_bool(deque *self);
dword deque_len(deque *self);
void deque_append(deque *self, byte value);

iter_deque *iter_deque_call(deque *data);
iter_deque *iter_deque_new(void);
iter_deque *iter_deque_copy(iter_deque *self);
void iter_deque_del(iter_deque *self);
void iter_deque_init(iter_deque *self, deque *data);
byte iter_deque_current(iter_deque *self);
dword iter_deque_key(iter_deque *self);
void iter_deque_next(iter_deque *self);
void iter_deque_rewind(iter_deque *self);
void iter_deque_stop(iter_deque *self);
bool iter_deque_valid(iter_deque *self);

sdword int_ceildiv(sdword dividend, sdword divisor);
byte int_bit_length(dword number);
sdword int_mod(sdword dividend, sdword divisor);

void random_bytes(bytes *buffer);
dword random_range(dword stop);
byte random_choice(bytes *buffer);
void random_shuffle(bytes *buffer);

/* Key(data) -> Key instance
 * 
 * This class represents a Markov Encryption Key primitive. It allows for
 * easy key creation, checks for proper data construction, and helps with
 * encoding and decoding indexes based on cached internal tables.
 */

Key *Key_create(bytes *bytes_used, word chain_size);
Key *Key_call(list *data);
Key *Key_new(void);
Key *Key_copy(Key *self);
void Key_del(Key *self);
void Key_init(Key *self, list *data);
void Key_test_data(list *data);
void Key_make_vars(Key *self, list *data);
byte Key_calculate_offset(list *data, word prefix_len, bytes *base, word size);
list *Key_calculate_axes(list *data, word prefix_len, bytes *base, word size);
list *Key_calculate_decoder(bytes *base, word size, byte offset, bytes *order);
void Key_test_primer(Key *self, Primer *vector);
byte Key_encode(Key *self, deque *prefix, byte current);
byte Key_decode(Key *self, deque *prefix, byte current);
dword Key_calculate_sum(Key *self, deque *prefix);
list *Key_get_data(Key *self);
word Key_get_prefix_len(Key *self);
bytes *Key_get_base(Key *self);
bytes *Key_get_order(Key *self);

/* Primer(data) -> Primer instance
 * 
 * This class represents a Markov Encryption Primer primitive. It is very
 * important for starting both the encryption and decryption processes. A
 * method is provided for their easy creation with a related key.
 */

Primer *Primer_create(Key *primary);
Primer *Primer_call(bytes *data);
Primer *Primer_new(void);
Primer *Primer_copy(Primer *self);
void Primer_del(Primer *self);
void Primer_init(Primer *self, bytes *data);
void Primer_test_data(bytes *data);
void Primer_test_key(Primer *self, Key *primary);
bytes *Primer_get_data(Primer *self);

/* _Processor(key, primer) -> NotImplementedError exception
 * 
 * This class acts as a base for the encryption and decryption processes.
 * The given key is saved, and several tables are created along with an
 * index. Since it is abstract, calling the class will raise an exception.
 */

_Processor *_Processor_call(Key *primary, Primer *vector);
_Processor *_Processor_new(void);
_Processor *_Processor_copy(_Processor *self);
void _Processor_del(_Processor *self);
void _Processor_init(_Processor *self, Key *primary, Primer *vector);
bytes *_Processor_process(_Processor *self, bytes *data, void (*converter)(dict *encoder, byte value, Key *primary, deque *prefix, bytes *cache, dword offset));
Primer *_Processor_get_primer(_Processor *self);

/* Encrypter(key, primer) -> Encrypter instance
 * 
 * This class represents a state-aware encryption engine that can be fed
 * data and will return a stream of coherent cipher-text. An index is
 * maintained, and a state-continuation primer can be retrieved at will.
 */

#define Encrypter_call(primary, vector) _Processor_call(primary, vector)
#define Encrypter_copy(self) _Processor_copy(self)
#define Encrypter_del(self) _Processor_del(self)
bytes *Encrypter_process(Encrypter *self, bytes *data);
void Encrypter_convert(dict *encoder, byte value, Key *primary, deque *prefix, bytes *cache, dword offset);
#define Encrypter_get_primer(self) _Processor_get_primer(self)

/* Decrypter(key, primer) -> Decrypter instance
 * 
 * This class represents a state-aware decryption engine that can be fed
 * data and will return a stream of coherent plain-text. An index is
 * maintained, and a state-continuation primer can be retrieved at will.
 */

#define Decrypter_call(primary, vector) _Processor_call(primary, vector)
#define Decrypter_copy(self) _Processor_copy(self)
#define Decrypter_del(self) _Processor_del(self)
bytes *Decrypter_process(Decrypter *self, bytes *data);
void Decrypter_convert(dict *encoder, byte value, Key *primary, deque *prefix, bytes *cache, dword offset);
#define Decrypter_get_primer(self) _Processor_get_primer(self)

int main(int argc, char *argv[])
{
    {
        bytes *buffer, *other, *repr;
        char *value;
        range *counter;
        dword offset;
        set *group;
        buffer = bytes_call(15);
        value = bytes_hex(buffer);
        printf("%s\n", value);
        del(value);
        value = bytes_repr(buffer);
        printf("%s\n", value);
        del(value);
        assert(bytes_bool(buffer), "Buffer should be true!");
        assert(bytes_len(buffer) == 15, "Buffer length is wrong!");
        bytes_del(buffer);
        buffer = bytes_from_buffer(0, NULL);
        assert(!bytes_bool(buffer), "Buffer should be false!");
        assert(bytes_len(buffer) == 0, "Buffer length is wrong!");
        bytes_del(buffer);
        buffer = bytes_from_string("Hello, world!");
        value = bytes_repr(buffer);
        printf("%s\n", value);
        del(value);
        repr = bytes_call(1);
        counter = range_stop(256);
        foreach(byte, code, range, counter);
            bytes_setitem(repr, 0, code);
            value = bytes_repr(repr);
            printf("%s\n", value);
            del(value);
        end_foreach(code, range);
        bytes_del(repr);
        range_del(counter);
        other = bytes_deepcopy(buffer);
        assert(bytes_getitem(buffer, 0) == 'H' && bytes_getitem(other, 0) == 'H', "Buffers are not valid!");
        bytes_setitem(other, 0, 'J');
        assert(bytes_getitem(buffer, 0) == 'H' && bytes_getitem(other, 0) == 'J', "Buffers are not valid!");
        bytes_del(other);
        assert(bytes_find(buffer, '!', &offset), "Character not found!");
        assert(offset == 12, "Character in wrong position!");
        assert(!bytes_find(buffer, '.', &offset), "Character was found!");
        assert(bytes_index(buffer, ',') == 5, "Character not found as expected!");
        bytes_rotate(buffer, 4);
        value = bytes_repr(buffer);
        printf("%s\n", value);
        del(value);
        bytes_rotate(buffer, bytes_len(buffer) - 4);
        value = bytes_repr(buffer);
        printf("%s\n", value);
        del(value);
        bytes_sort(buffer);
        value = bytes_repr(buffer);
        printf("%s\n", value);
        del(value);
        bytes_del(buffer);
        group = set_call();
        buffer = bytes_from_set(group);
        set_del(group);
        assert(!bytes_bool(buffer), "Buffer should be empty!");
        bytes_del(buffer);
        buffer = bytes_from_string("ytpme");
        group = set_from_bytes(buffer);
        bytes_del(buffer);
        buffer = bytes_from_set(group);
        set_del(group);
        value = bytes_repr(buffer);
        bytes_del(buffer);
        printf("%s\n", value);
        del(value);
        buffer = bytes_from_string("pensAcolA");
        assert(bytes_len(buffer) == 9, "Buffer should be size nine!");
        group = set_from_bytes(buffer);
        bytes_del(buffer);
        assert(set_len(group) == 8, "Group should be size eight!");
        buffer = bytes_from_set(group);
        set_del(group);
        assert(bytes_len(buffer) == 8, "Buffer should be size eight!");
        value = bytes_repr(buffer);
        bytes_del(buffer);
        printf("%s\n", value);
        del(value);
        buffer = bytes_from_string("");
        other = bytes_from_string("");
        assert(bytes_cmp(buffer, other) == 0, "Comparison should return zero!");
        assert(!bytes_lt(buffer, other), "Is not less than!");
        assert(bytes_le(buffer, other), "Is less than or equal!");
        assert(bytes_eq(buffer, other), "Is equal!");
        assert(!bytes_ne(buffer, other), "Is equal!");
        assert(!bytes_gt(buffer, other), "Is not greater than!");
        assert(bytes_ge(buffer, other), "Is greater than or equal!");
        assert(bytes_cmp(other, buffer) == 0, "Comparison should return zero!");
        assert(!bytes_lt(other, buffer), "Is not less than!");
        assert(bytes_le(other, buffer), "Is less than or equal!");
        assert(bytes_eq(other, buffer), "Is equal!");
        assert(!bytes_ne(other, buffer), "Is equal!");
        assert(!bytes_gt(other, buffer), "Is not greater than!");
        assert(bytes_ge(other, buffer), "Is greater than or equal!");
        bytes_del(buffer);
        bytes_del(other);
        buffer = bytes_from_string("Hello");
        other = bytes_from_string("Hello");
        assert(bytes_cmp(buffer, other) == 0, "Comparison should return zero!");
        assert(!bytes_lt(buffer, other), "Is not less than!");
        assert(bytes_le(buffer, other), "Is less than or equal!");
        assert(bytes_eq(buffer, other), "Is equal!");
        assert(!bytes_ne(buffer, other), "Is equal!");
        assert(!bytes_gt(buffer, other), "Is not greater than!");
        assert(bytes_ge(buffer, other), "Is greater than or equal!");
        assert(bytes_cmp(other, buffer) == 0, "Comparison should return zero!");
        assert(!bytes_lt(other, buffer), "Is not less than!");
        assert(bytes_le(other, buffer), "Is less than or equal!");
        assert(bytes_eq(other, buffer), "Is equal!");
        assert(!bytes_ne(other, buffer), "Is equal!");
        assert(!bytes_gt(other, buffer), "Is not greater than!");
        assert(bytes_ge(other, buffer), "Is greater than or equal!");
        bytes_del(buffer);
        bytes_del(other);
        buffer = bytes_from_string("arch");
        other = bytes_from_string("archer");
        assert(bytes_cmp(buffer, other) == -1, "Comparison should return -1!");
        assert(bytes_lt(buffer, other), "Is less than!");
        assert(bytes_le(buffer, other), "Is less than or equal!");
        assert(!bytes_eq(buffer, other), "Is not equal!");
        assert(bytes_ne(buffer, other), "Is not equal!");
        assert(!bytes_gt(buffer, other), "Is not greater than!");
        assert(!bytes_ge(buffer, other), "Is not greater than or equal!");
        assert(bytes_cmp(other, buffer) == +1, "Comparison should return +1!");
        assert(!bytes_lt(other, buffer), "Is not less than!");
        assert(!bytes_le(other, buffer), "Is not less than or equal!");
        assert(!bytes_eq(other, buffer), "Is not equal!");
        assert(bytes_ne(other, buffer), "Is not equal!");
        assert(bytes_gt(other, buffer), "Is greater than!");
        assert(bytes_ge(other, buffer), "Is greater than or equal!");
        bytes_del(buffer);
        bytes_del(other);
        buffer = bytes_from_string("applet");
        other = bytes_from_string("application");
        assert(bytes_cmp(buffer, other) == -1, "Comparison should return -1!");
        assert(bytes_lt(buffer, other), "Is less than!");
        assert(bytes_le(buffer, other), "Is less than or equal!");
        assert(!bytes_eq(buffer, other), "Is not equal!");
        assert(bytes_ne(buffer, other), "Is not equal!");
        assert(!bytes_gt(buffer, other), "Is not greater than!");
        assert(!bytes_ge(buffer, other), "Is not greater than or equal!");
        assert(bytes_cmp(other, buffer) == +1, "Comparison should return +1!");
        assert(!bytes_lt(other, buffer), "Is not less than!");
        assert(!bytes_le(other, buffer), "Is not less than or equal!");
        assert(!bytes_eq(other, buffer), "Is not equal!");
        assert(bytes_ne(other, buffer), "Is not equal!");
        assert(bytes_gt(other, buffer), "Is greater than!");
        assert(bytes_ge(other, buffer), "Is greater than or equal!");
        bytes_del(buffer);
        bytes_del(other);
    }
    {
        bytes *buffer;
        byte state;
        buffer = bytes_from_string("Information Technology");
        foreach(byte, value, bytes, buffer);
            printf("%c", value);
        end_foreach(value, bytes);
        printf("\n");
        state = 0;
        foreach(byte, value, bytes, buffer);
            printf("buffer[%02i] == '%c'\n", iter_key(value, bytes), value);
            switch (value)
            {
                case 'l':
                    iter_stop(value, bytes);
                    break;
                case 'i':
                    if (state < 2)
                    {
                        iter_rewind(value, bytes);
                        state += 1;
                        printf("Rewinding to '%c'\n", iter_current(value, bytes));
                    }
            }
        end_foreach(value, bytes);
        bytes_del(buffer);
    }
    {
        range *counter;
        counter = range_call(10, 20, 3);
        assert(counter->start == 10 && counter->stop == 20 && counter->step == 3, "Range values are wrong!");
        range_del(counter);
        counter = range_start_stop(30, 40);
        assert(counter->start == 30 && counter->stop == 40 && counter->step == 1, "Range values are wrong!");
        range_del(counter);
        counter = range_start_stop(60, 50);
        assert(counter->start == 60 && counter->stop == 50 && counter->step == -1, "Range values are wrong!");
        range_del(counter);
        counter = range_stop(70);
        assert(counter->start == 0 && counter->stop == 70 && counter->step == 1, "Range values are wrong!");
        range_del(counter);
        counter = range_stop(-80);
        assert(counter->start == 0 && counter->stop == -80 && counter->step == -1, "Range values are wrong!");
        range_del(counter);
    }
    {
        range *counter;
        counter = range_stop(10);
        foreach(sdword, value, range, counter);
            printf(" %i", value);
        end_foreach(value, range);
        printf("\n");
        range_del(counter);
        counter = range_start_stop(9, -1);
        foreach(sdword, value, range, counter);
            printf(" %i", value);
        end_foreach(value, range);
        printf("\n");
        range_del(counter);
        counter = range_call(10, 20, 2);
        foreach(sdword, value, range, counter);
            printf(" %i", value);
        end_foreach(value, range);
        printf("\n");
        range_del(counter);
        counter = range_call(10, 21, 2);
        foreach(sdword, value, range, counter);
            printf(" %i", value);
        end_foreach(value, range);
        printf("\n");
        range_del(counter);
    }
    {
        set *group, *other, *answer;
        bytes *buffer;
        group = set_call();
        assert(!set_bool(group), "Group should be false!");
        assert(set_len(group) == 0, "Length should be zero!");
        set_del(group);
        buffer = bytes_from_string("Hello, world!");
        group = set_from_bytes(buffer);
        bytes_del(buffer);
        assert(set_bool(group), "Group should be true!");
        assert(set_len(group) == 10, "Length should be ten!");
        assert(!set_contains(group, ';'), "';' is not in group!");
        assert(set_contains(group, ','), "',' is in group!");
        assert(set_issubset(group, group), "Group should be subset of itself!");
        assert(set_issuperset(group, group), "Group should be superset of itself!");
        buffer = bytes_from_string("Hello world");
        other = set_from_bytes(buffer);
        bytes_del(buffer);
        assert(set_issubset(other, group), "Other is subset of group!");
        assert(!set_issuperset(other, group), "Other is not superset of group!");
        set_del(group);
        set_del(other);
        buffer = bytes_from_string("ABCDEFG");
        group = set_from_bytes(buffer);
        bytes_del(buffer);
        buffer = bytes_from_string("EFGHI");
        other = set_from_bytes(buffer);
        bytes_del(buffer);
        answer = set_union(group, other);
        assert(set_len(answer) == 9, "Set should be size nine!");
        set_del(answer);
        answer = set_intersection(group, other);
        assert(set_len(answer) == 3, "Set should be size three!");
        set_del(answer);
        answer = set_difference(group, other);
        assert(set_len(answer) == 4, "Set should be size four!");
        set_del(answer);
        answer = set_difference(other, group);
        assert(set_len(answer) == 2, "Set should be size two!");
        set_del(answer);
        answer = set_symmetric_difference(group, other);
        assert(set_len(answer) == 6, "Set should be size size!");
        set_del(answer);
        answer = set_deepcopy(group);
        assert(set_len(answer) == 7, "Set should be size seven!");
        set_del(answer);
        assert(set_len(other) == 5, "Set should be size five!");
        set_add(other, 'Z');
        assert(set_len(other) == 6, "Set should be size size!");
        set_add(other, 'Z');
        assert(set_len(other) == 6, "Set should be size size!");
        set_remove(other, 'Z');
        assert(set_len(other) == 5, "Set should be size five!");
        set_discard(other, 'Z');
        assert(set_len(other) == 5, "Set should be size five!");
        set_clear(other);
        assert(set_len(other) == 0, "Set should be size zero!");
        answer = set_mutate(other, group, true);
        assert(set_len(answer) == 7, "Set should be size seven!");
        set_del(answer);
        set_del(group);
        set_del(other);
    }
    {
        bytes *buffer;
        set *group;
        char *repr;
        iter_set *iter;
        bool state;
        byte value;
        buffer = bytes_from_string("United States of America");
        group = set_from_bytes(buffer);
        bytes_del(buffer);
        buffer = bytes_call(1);
        foreach(bool, member, set, group);
            bytes_setitem(buffer, 0, iter_key(member, set));
            repr = bytes_repr(buffer);
            printf("%s = %s\n", repr, member ? "True" : "False");
            del(repr);
        end_foreach(member, set);
        for (iter = set_iter(group), iter_set_rewind_member(iter); iter_set_valid(iter); iter_set_next_member(iter))
        {
            bytes_setitem(buffer, 0, iter_set_current_member(iter));
            repr = bytes_repr(buffer);
            printf("%s\n", repr);
            del(repr);
        }
        bytes_del(buffer);
        for (state = false, iter_set_rewind_member(iter); iter_set_valid(iter); iter_set_next_member(iter))
        {
            value = iter_set_current_member(iter);
            if (value == ' ' && !state)
            {
                set_remove(group, 'A');
                set_remove(group, 'U');
                set_remove(group, 'c');
            }
            else if (value == 'e')
            {
                if (!state)
                {
                    set_remove(group, 'S');
                    set_remove(group, 'a');
                    set_remove(group, 'd');
                    set_add(group, '\0');
                    state = true;
                    iter_set_rewind_member(iter);
                }
            }
            else if (value == 'i')
            {
                set_remove(group, 's');
                iter_set_next_member(iter);
                iter_set_next_member(iter);
            }
            else
                printf("%c", value);
        }
        iter_set_del(iter);
        printf("\n");
        set_del(group);
    }
    {
        dict *map, *reversed;
        range *counter;
        bytes *data, *test, *aux;
        char *repr;
        map = dict_call();
        counter = range_stop(256);
        test = bytes_call(1);
        foreach(byte, key, range, counter);
            foreach(byte, value, range, counter);
                assert(!dict_bool(map), "Dictionary should be empty!");
                assert(dict_len(map) == 0, "Dictionary size should be zero!");
                data = dict_keys(map);
                assert(!bytes_bool(data), "Keys should be empty!");
                bytes_del(data);
                data = dict_values(map);
                assert(!bytes_bool(data), "Values should be empty!");
                bytes_del(data);
                assert(!dict_contains(map, key), "Key should not be in mapping object!");
                dict_setitem(map, key, value);
                assert(dict_getitem(map, key) == value, "Stored value is invalid!");
                assert(dict_bool(map), "Dictionary should not be empty!");
                assert(dict_len(map) == 1, "Dictionary size should be one!");
                data = dict_keys(map);
                bytes_setitem(test, 0, key);
                assert(bytes_eq(data, test), "Keys are invalid!");
                bytes_del(data);
                data = dict_values(map);
                bytes_setitem(test, 0, value);
                assert(bytes_eq(data, test), "Values are invalid!");
                bytes_del(data);
                assert(dict_contains(map, key), "Key should be in mapping object!");
                dict_delitem(map, key);
            end_foreach(value, range);
        end_foreach(key, range);
        bytes_del(test);
        range_del(counter);
        dict_del(map);
        data = bytes_from_string("Testing");
        aux = bytes_from_string("Success");
        map = dict_from_pairs(data, aux);
        test = bytes_call(bytes_len(data));
        foreach(byte, character, bytes, data);
            bytes_setitem(test, iter_key(character, bytes), dict_getitem(map, character));
        end_foreach(character, bytes);
        repr = bytes_repr(test);
        printf("%s\n", repr);
        del(repr);
        assert(bytes_eq(test, aux), "Conversion was not successful!");
        reversed = dict_reversed(map);
        assert(reversed == NULL, "Should not have reversed dictionary!");
        dict_del(map);
        bytes_del(aux);
        aux = bytes_from_string("Hopeful");
        map = dict_from_pairs(data, aux);
        reversed = dict_reversed(map);
        assert_not_null(reversed);
        dict_del(map);
        foreach(byte, character, bytes, aux);
            bytes_setitem(test, iter_key(character, bytes), dict_getitem(reversed, character));
        end_foreach(character, bytes);
        assert(bytes_eq(test, data), "Conversion was not successful!");
        dict_del(reversed);
        bytes_del(test);
        bytes_del(aux);
        bytes_del(data);
    }
    {
        bytes *keys, *values;
        dict *map;
        bool state;
        keys = bytes_from_string("ABC");
        values = bytes_from_string("XYZ");
        map = dict_from_pairs(keys, values);
        bytes_del(keys);
        bytes_del(values);
        state = false;
        foreach(byte, value, dict, map);
            switch (value)
            {
                case 'X':
                    assert(iter_key(value, dict) == 'A', "Key is wrong!");
                    if (state)
                        dict_delitem(map, 'B');
                    break;
                case 'Y':
                    assert(iter_key(value, dict) == 'B', "Key is wrong!");
                    dict_setitem(map, '0', 'A');
                    dict_setitem(map, 'D', '!');
                    state = true;
                    iter_rewind(value, dict);
                    break;
                case 'Z':
                    assert(iter_key(value, dict) == 'C', "Key is wrong!");
                    iter_stop(value, dict);
                    break;
                default:
                    raise("Logic", "Line should never be executed!");
            }
        end_foreach(value, dict);
        assert(dict_len(map) == 4, "Dictionary size should be four!");
        assert(dict_contains(map, 'D'), "'D' key is missing from dictionary!");
        assert(!dict_contains(map, 'B'), "'B' key should not be in dictionary!");
        dict_del(map);
    }
    {
        list *array;
        range *counter;
        array = list_call(0);
        assert(!list_bool(array), "List should be false!");
        assert(list_len(array) == 0, "List length should be zero!");
        list_del(array);
        array = list_call(4);
        assert(list_bool(array), "List should be true!");
        assert(list_len(array) == 4, "List length should be four!");
        counter = range_stop(list_len(array));
        foreach(byte, offset, range, counter);
            assert(list_getitem(array, offset) == NULL, "Item should be null!");
        end_foreach(offset, range);
        list_setitem(array, 3, "!\n");
        list_setitem(array, 2, "world");
        list_setitem(array, 1, ", ");
        list_setitem(array, 0, "Hello");
        foreach(byte, offset, range, counter);
            printf(list_getitem(array, offset));
        end_foreach(offset, range);
        range_del(counter);
        list_del(array);
    }
    {
        list *array;
        bytes *buffer;
        char *repr;
        array = list_call(4);
        buffer = bytes_from_string("Hello");
        list_setitem(array, 0, bytes_copy(buffer));
        bytes_del(buffer);
        buffer = bytes_from_string(", ");
        list_setitem(array, 1, bytes_copy(buffer));
        bytes_del(buffer);
        buffer = bytes_from_string("world");
        list_setitem(array, 2, bytes_copy(buffer));
        bytes_del(buffer);
        buffer = bytes_from_string("!\n");
        list_setitem(array, 3, bytes_copy(buffer));
        bytes_del(buffer);
        foreach(bytes *, value, list, array);
            repr = bytes_repr(value);
            bytes_del(value);
            printf("%i: %s\n", iter_key(value, list), repr);
            del(repr);
        end_foreach(value, list);
        list_del(array);
    }
    {
        range *counter;
        bytes *buffer;
        deque *index;
        counter = range_stop(1 << 10);
        foreach(word, size, range, counter);
            buffer = bytes_call(size);
            index = deque_call(buffer);
            foreach(word, value, range, counter);
                deque_append(index, value & 0xFF);
                assert(deque_bool(index) == bytes_bool(buffer), "Bool values should match!");
                assert(deque_len(index) == bytes_len(buffer), "Length values should match!");
            end_foreach(value, range);
            deque_del(index);
            bytes_del(buffer);
        end_foreach(size, range);
        range_del(counter);
    }
    {
        bytes *buffer;
        range *counter;
        deque *index;
        buffer = bytes_call(26);
        counter = range_stop(bytes_len(buffer));
        foreach(byte, offset, range, counter);
            bytes_setitem(buffer, offset, 'A' + offset);
        end_foreach(offset, range);
        index = deque_call(buffer);
        bytes_del(buffer);
        foreach(byte, offset, range, counter);
            deque_append(index, 'Z' - offset);
            foreach(byte, character, deque, index);
                printf("%c", character);
            end_foreach(character, deque);
            printf("\n");
        end_foreach(offset, range);
        deque_del(index);
        range_del(counter);
    }
    {
        range *counter;
        word quotient;
        counter = range_start_stop(1, 1 << 16);
        foreach(word, dividend, range, counter);
            foreach(word, divisor, range, counter);
                quotient = dividend / divisor;
                if ((double)quotient != (double)divisor / dividend)
                    quotient += 1;
                assert(int_ceildiv(divisor, dividend) == quotient, "Function int_ceildiv is not valid!");
            end_foreach(divisor, range);
        end_foreach(dividend, range);
        range_del(counter);
        counter = range_start_stop(1, 32);
        foreach(byte, bits, range, counter);
            assert(int_bit_length(1 << (bits - 1)) == bits, "Bit length is incorrect!");
            assert(int_bit_length((1 << bits) - 1) == bits, "Bit length is incorrect!");
        end_foreach(bits, range);
        range_del(counter);
        assert(int_mod(5, 5) == 0, "5 % 5 should equal 0!");
        assert(int_mod(4, 5) == 4, "4 % 5 should equal 4!");
        assert(int_mod(3, 5) == 3, "3 % 5 should equal 3!");
        assert(int_mod(2, 5) == 2, "2 % 5 should equal 2!");
        assert(int_mod(1, 5) == 1, "1 % 5 should equal 1!");
        assert(int_mod(0, 5) == 0, "0 % 5 should equal 0!");
        assert(int_mod(-1, 5) == 4, "-1 % 5 should equal 4!");
        assert(int_mod(-2, 5) == 3, "-2 % 5 should equal 3!");
        assert(int_mod(-3, 5) == 2, "-3 % 5 should equal 2!");
        assert(int_mod(-4, 5) == 1, "-4 % 5 should equal 1!");
        assert(int_mod(-5, 5) == 0, "-5 % 5 should equal 0!");
        assert(int_mod(5, 4) == 1, "5 % 4 should equal 1!");
        assert(int_mod(4, 4) == 0, "4 % 4 should equal 0!");
        assert(int_mod(3, 4) == 3, "3 % 4 should equal 3!");
        assert(int_mod(2, 4) == 2, "2 % 4 should equal 2!");
        assert(int_mod(1, 4) == 1, "1 % 4 should equal 1!");
        assert(int_mod(0, 4) == 0, "0 % 4 should equal 0!");
        assert(int_mod(-1, 4) == 3, "-1 % 4 should equal 3!");
        assert(int_mod(-2, 4) == 2, "-2 % 4 should equal 2!");
        assert(int_mod(-3, 4) == 1, "-3 % 4 should equal 1!");
        assert(int_mod(-4, 4) == 0, "-4 % 4 should equal 0!");
        assert(int_mod(-5, 4) == 3, "-5 % 4 should equal 3!");
        assert(int_mod(5, 3) == 2, "5 % 3 should equal 2!");
        assert(int_mod(4, 3) == 1, "4 % 3 should equal 1!");
        assert(int_mod(3, 3) == 0, "3 % 3 should equal 0!");
        assert(int_mod(2, 3) == 2, "2 % 3 should equal 2!");
        assert(int_mod(1, 3) == 1, "1 % 3 should equal 1!");
        assert(int_mod(0, 3) == 0, "0 % 3 should equal 0!");
        assert(int_mod(-1, 3) == 2, "-1 % 3 should equal 2!");
        assert(int_mod(-2, 3) == 1, "-2 % 3 should equal 1!");
        assert(int_mod(-3, 3) == 0, "-3 % 3 should equal 0!");
        assert(int_mod(-4, 3) == 2, "-4 % 3 should equal 2!");
        assert(int_mod(-5, 3) == 1, "-5 % 3 should equal 1!");
        assert(int_mod(5, 2) == 1, "5 % 2 should equal 1!");
        assert(int_mod(4, 2) == 0, "4 % 2 should equal 0!");
        assert(int_mod(3, 2) == 1, "3 % 2 should equal 1!");
        assert(int_mod(2, 2) == 0, "2 % 2 should equal 0!");
        assert(int_mod(1, 2) == 1, "1 % 2 should equal 1!");
        assert(int_mod(0, 2) == 0, "0 % 2 should equal 0!");
        assert(int_mod(-1, 2) == 1, "-1 % 2 should equal 1!");
        assert(int_mod(-2, 2) == 0, "-2 % 2 should equal 0!");
        assert(int_mod(-3, 2) == 1, "-3 % 2 should equal 1!");
        assert(int_mod(-4, 2) == 0, "-4 % 2 should equal 0!");
        assert(int_mod(-5, 2) == 1, "-5 % 2 should equal 1!");
        assert(int_mod(5, 1) == 0, "5 % 1 should equal 0!");
        assert(int_mod(4, 1) == 0, "4 % 1 should equal 0!");
        assert(int_mod(3, 1) == 0, "3 % 1 should equal 0!");
        assert(int_mod(2, 1) == 0, "2 % 1 should equal 0!");
        assert(int_mod(1, 1) == 0, "1 % 1 should equal 0!");
        assert(int_mod(0, 1) == 0, "0 % 1 should equal 0!");
        assert(int_mod(-1, 1) == 0, "-1 % 1 should equal 0!");
        assert(int_mod(-2, 1) == 0, "-2 % 1 should equal 0!");
        assert(int_mod(-3, 1) == 0, "-3 % 1 should equal 0!");
        assert(int_mod(-4, 1) == 0, "-4 % 1 should equal 0!");
        assert(int_mod(-5, 1) == 0, "-5 % 1 should equal 0!");
        assert(int_mod(5, -1) == 0, "5 % -1 should equal 0!");
        assert(int_mod(4, -1) == 0, "4 % -1 should equal 0!");
        assert(int_mod(3, -1) == 0, "3 % -1 should equal 0!");
        assert(int_mod(2, -1) == 0, "2 % -1 should equal 0!");
        assert(int_mod(1, -1) == 0, "1 % -1 should equal 0!");
        assert(int_mod(0, -1) == 0, "0 % -1 should equal 0!");
        assert(int_mod(-1, -1) == 0, "-1 % -1 should equal 0!");
        assert(int_mod(-2, -1) == 0, "-2 % -1 should equal 0!");
        assert(int_mod(-3, -1) == 0, "-3 % -1 should equal 0!");
        assert(int_mod(-4, -1) == 0, "-4 % -1 should equal 0!");
        assert(int_mod(-5, -1) == 0, "-5 % -1 should equal 0!");
        assert(int_mod(5, -2) == -1, "5 % -2 should equal -1!");
        assert(int_mod(4, -2) == 0, "4 % -2 should equal 0!");
        assert(int_mod(3, -2) == -1, "3 % -2 should equal -1!");
        assert(int_mod(2, -2) == 0, "2 % -2 should equal 0!");
        assert(int_mod(1, -2) == -1, "1 % -2 should equal -1!");
        assert(int_mod(0, -2) == 0, "0 % -2 should equal 0!");
        assert(int_mod(-1, -2) == -1, "-1 % -2 should equal -1!");
        assert(int_mod(-2, -2) == 0, "-2 % -2 should equal 0!");
        assert(int_mod(-3, -2) == -1, "-3 % -2 should equal -1!");
        assert(int_mod(-4, -2) == 0, "-4 % -2 should equal 0!");
        assert(int_mod(-5, -2) == -1, "-5 % -2 should equal -1!");
        assert(int_mod(5, -3) == -1, "5 % -3 should equal -1!");
        assert(int_mod(4, -3) == -2, "4 % -3 should equal -2!");
        assert(int_mod(3, -3) == 0, "3 % -3 should equal 0!");
        assert(int_mod(2, -3) == -1, "2 % -3 should equal -1!");
        assert(int_mod(1, -3) == -2, "1 % -3 should equal -2!");
        assert(int_mod(0, -3) == 0, "0 % -3 should equal 0!");
        assert(int_mod(-1, -3) == -1, "-1 % -3 should equal -1!");
        assert(int_mod(-2, -3) == -2, "-2 % -3 should equal -2!");
        assert(int_mod(-3, -3) == 0, "-3 % -3 should equal 0!");
        assert(int_mod(-4, -3) == -1, "-4 % -3 should equal -1!");
        assert(int_mod(-5, -3) == -2, "-5 % -3 should equal -2!");
        assert(int_mod(5, -4) == -3, "5 % -4 should equal -3!");
        assert(int_mod(4, -4) == 0, "4 % -4 should equal 0!");
        assert(int_mod(3, -4) == -1, "3 % -4 should equal -1!");
        assert(int_mod(2, -4) == -2, "2 % -4 should equal -2!");
        assert(int_mod(1, -4) == -3, "1 % -4 should equal -3!");
        assert(int_mod(0, -4) == 0, "0 % -4 should equal 0!");
        assert(int_mod(-1, -4) == -1, "-1 % -4 should equal -1!");
        assert(int_mod(-2, -4) == -2, "-2 % -4 should equal -2!");
        assert(int_mod(-3, -4) == -3, "-3 % -4 should equal -3!");
        assert(int_mod(-4, -4) == 0, "-4 % -4 should equal 0!");
        assert(int_mod(-5, -4) == -1, "-5 % -4 should equal -1!");
        assert(int_mod(5, -5) == 0, "5 % -5 should equal 0!");
        assert(int_mod(4, -5) == -1, "4 % -5 should equal -1!");
        assert(int_mod(3, -5) == -2, "3 % -5 should equal -2!");
        assert(int_mod(2, -5) == -3, "2 % -5 should equal -3!");
        assert(int_mod(1, -5) == -4, "1 % -5 should equal -4!");
        assert(int_mod(0, -5) == 0, "0 % -5 should equal 0!");
        assert(int_mod(-1, -5) == -1, "-1 % -5 should equal -1!");
        assert(int_mod(-2, -5) == -2, "-2 % -5 should equal -2!");
        assert(int_mod(-3, -5) == -3, "-3 % -5 should equal -3!");
        assert(int_mod(-4, -5) == -4, "-4 % -5 should equal -4!");
        assert(int_mod(-5, -5) == 0, "-5 % -5 should equal 0!");
    }
    {
        bytes *buffer, *hex;
        char *repr;
        range *counter;
        word stop;
        buffer = bytes_call(15);
        repr = bytes_repr(buffer);
        printf("%s\n", repr);
        del(repr);
        counter = range_stop(bytes_len(buffer));
        foreach(byte, label, range, counter);
            random_bytes(buffer);
            repr = bytes_repr(buffer);
            printf("%02i: %s\n", label + 1, repr);
            del(repr);
        end_foreach(label, range);
        foreach(byte, bits, range, counter);
            stop = random_range(1 << (bits + 2));
            printf("random_range(%i) -> %i\n", stop, random_range(stop));
        end_foreach(bits, range);
        hex = bytes_from_string("ABCDEF");
        foreach(byte, offset, range, counter);
            bytes_setitem(buffer, offset, random_choice(hex));
        end_foreach(offset, range);
        range_del(counter);
        repr = bytes_repr(buffer);
        bytes_del(buffer);
        printf("%s\n", repr);
        del(repr);
        repr = bytes_repr(hex);
        printf("%s\n", repr);
        del(repr);
        random_shuffle(hex);
        repr = bytes_repr(hex);
        bytes_del(hex);
        printf("%s\n", repr);
        del(repr);
    }
    {
        bytes *used, *block;
        Key *fob;
        char *repr;
        list *array;
        deque *prefix;
        used = bytes_from_string("Source Code");
        Key_del(Key_create(used, 9000));
        fob = Key_create(used, 9);
        repr = bytes_repr(Key_get_base(fob));
        printf("%s\n", repr);
        del(repr);
        repr = bytes_repr(Key_get_order(fob));
        printf("%s\n", repr);
        del(repr);
        foreach(bytes *, block, list, Key_get_data(fob));
            repr = bytes_repr(block);
            printf("%s\n", repr);
            del(repr);
        end_foreach(block, list);
        assert(Key_get_prefix_len(fob) == 8, "Prefix length should be eight!");
        Key_del(fob);
        bytes_del(used);
        block = bytes_from_string("ejpszgwufrdmxbhkcatvolnyqi");
        array = list_call(4);
        list_setitem(array, 0, block);
        list_setitem(array, 1, block);
        list_setitem(array, 2, block);
        list_setitem(array, 3, block);
        fob = Key_call(array);
        list_del(array);
        bytes_del(block);
        block = bytes_from_string("\1\2\3");
        prefix = deque_call(block);
        bytes_del(block);
        assert(Key_encode(fob, prefix, 4) == 'd', "Key encode failed!");
        assert(Key_decode(fob, prefix, 4) == 'u', "Key decode failed!");
        deque_append(prefix, 4);
        assert(Key_encode(fob, prefix, 5) == 'h', "Key encode failed!");
        assert(Key_decode(fob, prefix, 5) == 'z', "Key decode failed!");
        deque_append(prefix, 5);
        assert(Key_encode(fob, prefix, 6) == 't', "Key encode failed!");
        assert(Key_decode(fob, prefix, 6) == 't', "Key decode failed!");
        deque_append(prefix, 6);
        assert(Key_encode(fob, prefix, 7) == 'n', "Key encode failed!");
        assert(Key_decode(fob, prefix, 7) == 'z', "Key decode failed!");
        deque_append(prefix, 7);
        assert(Key_encode(fob, prefix, 8) == 'e', "Key encode failed!");
        assert(Key_decode(fob, prefix, 8) == 'h', "Key decode failed!");
        deque_del(prefix);
        Key_del(fob);
    }
    {
        bytes *bytes_used;
        Key *primary;
        Primer *vector;
        bytes_used = bytes_from_string("What is C code?");
        primary = Key_create(bytes_used, 256);
        bytes_del(bytes_used);
        vector = Primer_create(primary);
        Primer_test_key(vector, primary);
        Key_test_primer(primary, vector);
        Key_del(primary);
        assert(bytes_len(Primer_get_data(vector)) == 255, "Primer length is wrong!");
        Primer_del(vector);
    }
    {
        bytes *bytes_used;
        Key *primary;
        Primer *vector, *internal;
        _Processor *engine;
        bytes_used = bytes_from_string("qwerty");
        primary = Key_create(bytes_used, bytes_len(bytes_used));
        bytes_del(bytes_used);
        vector = Primer_create(primary);
        engine = _Processor_call(primary, vector);
        Key_del(primary);
        internal = _Processor_get_primer(engine);
        _Processor_del(engine);
        assert(bytes_eq(Primer_get_data(vector), Primer_get_data(internal)), "Primers should be equal!");
        Primer_del(vector);
        Primer_del(internal);
    }
    {
        bytes *block, *plain_text, *cypher_text, *decoded_text;
        list *array;
        Key *primary;
        Primer *vector;
        Encrypter *encoder;
        Decrypter *decoder;
        block = bytes_from_string("ABC");
        array = list_call(3);
        list_setitem(array, 0, block);
        list_setitem(array, 1, block);
        list_setitem(array, 2, block);
        primary = Key_call(array);
        list_del(array);
        bytes_del(block);
        block = bytes_from_string("AB");
        vector = Primer_call(block);
        bytes_del(block);
        encoder = Encrypter_call(primary, vector);
        plain_text = bytes_from_string("aCBAacbcAbcAcbAcCcCACAAaaBcccCBBBbBcCaCb");
        cypher_text = Encrypter_process(encoder, plain_text);
        block = bytes_from_string("aABAacbcBbcAcbAcCcBBBCCaaBcccABBAbAcBaCb");
        assert(bytes_eq(cypher_text, block), "Encryption failed!");
        bytes_del(block);
        decoder = Decrypter_call(primary, vector);
        decoded_text = Decrypter_process(decoder, cypher_text);
        assert(bytes_eq(decoded_text, plain_text), "Decryption failed!");
        bytes_del(decoded_text);
        Decrypter_del(decoder);
        bytes_del(cypher_text);
        bytes_del(plain_text);
        Encrypter_del(encoder);
        Primer_del(vector);
        Key_del(primary);
    }
    {
        range *progress, *counter;
        bytes *bytes_used, *plain_text, *cypher_text, *decoded_text;
        char *repr;
        Key *primary;
        Primer *vector;
        Encrypter *encoder;
        Decrypter *decoder;
        progress = range_stop(10);
        foreach(byte, percentage, range, progress);
            printf("[ %i0%% ]\n", percentage);
            bytes_used = bytes_call(random_range(10) + 1);
            repr = bytes_repr(bytes_used);
            printf("  [1] Bytes used: %s\n", repr);
            del(repr);
            random_bytes(bytes_used);
            repr = bytes_repr(bytes_used);
            printf("  [2] Bytes used: %s\n", repr);
            del(repr);
            primary = Key_create(bytes_used, random_range(9) + 2);
            printf("  [3] Key data:\n");
            foreach(bytes *, block, list, Key_get_data(primary));
                repr = bytes_repr(block);
                printf("    [4] %s\n", repr);
                del(repr);
            end_foreach(block, list);
            vector = Primer_create(primary);
            repr = bytes_repr(Primer_get_data(vector));
            printf("  [5] Primer data: %s\n", repr);
            del(repr);
            encoder = Encrypter_call(primary, vector);
            decoder = Decrypter_call(primary, vector);
            counter = range_stop(random_range(10) + 1);
            foreach(byte, junk, range, counter);
                junk ^= junk;
                plain_text = bytes_call(random_range(20) + 1);
                repr = bytes_repr(plain_text);
                printf("    [6] Plain text: %s\n", repr);
                del(repr);
                random_bytes(plain_text);
                repr = bytes_repr(plain_text);
                printf("    [6] Plain text: %s\n", repr);
                del(repr);
                cypher_text = Encrypter_process(encoder, plain_text);
                repr = bytes_repr(cypher_text);
                printf("    [7] Cypher text: %s\n", repr);
                del(repr);
                decoded_text = Decrypter_process(decoder, cypher_text);
                repr = bytes_repr(decoded_text);
                printf("    [8] Decoded text: %s\n", repr);
                del(repr);
                assert(bytes_eq(decoded_text, plain_text), "Processing failed!");
                bytes_del(decoded_text);
                bytes_del(cypher_text);
                bytes_del(plain_text);
            end_foreach(junk, range);
            range_del(counter);
            Decrypter_del(decoder);
            Encrypter_del(encoder);
            Primer_del(vector);
            Key_del(primary);
            bytes_del(bytes_used);
        end_foreach(percentage, range);
        range_del(progress);
        printf("Closed!\n");
    }
    printf("\nobject_new_count = %i\nobject_del_count = %i\nobjects_leftover = %i\n----------------\nmemory_new_count = %i\nmemory_del_count = %i\nblocks_leftover = %i\n", object_new_count, object_del_count, object_new_count - object_del_count, memory_new_count, memory_del_count, memory_new_count - memory_del_count);
    return 0;
}

void _raise(char *file, int line, char *type, char *text)
{
    if (fprintf(stderr, "\nFILE: %s\nLINE: %i\nTYPE: %sError\nTEXT: %s", file, line, type, text) > 0)
        fflush(stderr);
    abort();
}

bytes *bytes_from_string(char *string)
{
    return bytes_from_buffer(strlen(string), (byte *)string);
}

bytes *bytes_from_buffer(dword size, byte *buffer)
{
    bytes *self;
    self = bytes_call(size);
    memcpy(self->data, buffer, size);
    return self;
}

bytes *bytes_from_set(set *group)
{
    bytes *self;
    byte offset;
    assert_not_null(group);
    self = bytes_call(set_len(group));
    offset = 0;
    foreach(bool, member, set, group);
        if (member)
            self->data[offset++] = iter_key(member, set);
    end_foreach(member, set);
    return self;
}

bytes *bytes_call(dword size)
{
    object_call(bytes, size);
}

bytes *bytes_new(void)
{
    object_new(bytes);
}

bytes *bytes_copy(bytes *self)
{
    object_copy(bytes);
}

void bytes_del(bytes *self)
{
    object_del(bytes);
        del(self->data);
    end_object_del();
}

void bytes_init(bytes *self, dword size)
{
    self->size = size;
    new(byte, self->data, size);
}

char *bytes_hex(bytes *self)
{
    char *buffer;
    dword finish, offset;
    assert_self();
    new(char, buffer, self->size * 3);
    finish = self->size - 1;
    foreach(byte, value, bytes, self);
        offset = iter_key(value, bytes);
        sprintf(buffer + offset * 3, (offset < finish ? "%02X " : "%02X"), value);
    end_foreach(value, bytes);
    return buffer;
}

char *bytes_repr(bytes *self)
{
    char *buffer, *destination, *source;
    byte length;
    char *repr[] = {"\\x00", "\\x01", "\\x02", "\\x03", "\\x04", "\\x05", "\\x06", "\\x07", "\\x08", "\\t", "\\n", "\\v", "\\f", "\\r", "\\x0E", "\\x0F", "\\x10", "\\x11", "\\x12", "\\x13", "\\x14", "\\x15", "\\x16", "\\x17", "\\x18", "\\x19", "\\x1A", "\\x1B", "\\x1C", "\\x1D", "\\x1E", "\\x1F", " ", "!", "\\\"", "#", "$", "%", "&", "'", "(", ")", "*", "+", ",", "-", ".", "/", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ":", ";", "<", "=", ">", "?", "@", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "[", "\\\\", "]", "^", "_", "`", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "{", "|", "}", "~", "\\x7F", "\\x80", "\\x81", "\\x82", "\\x83", "\\x84", "\\x85", "\\x86", "\\x87", "\\x88", "\\x89", "\\x8A", "\\x8B", "\\x8C", "\\x8D", "\\x8E", "\\x8F", "\\x90", "\\x91", "\\x92", "\\x93", "\\x94", "\\x95", "\\x96", "\\x97", "\\x98", "\\x99", "\\x9A", "\\x9B", "\\x9C", "\\x9D", "\\x9E", "\\x9F", "\\xA0", "\\xA1", "\\xA2", "\\xA3", "\\xA4", "\\xA5", "\\xA6", "\\xA7", "\\xA8", "\\xA9", "\\xAA", "\\xAB", "\\xAC", "\\xAD", "\\xAE", "\\xAF", "\\xB0", "\\xB1", "\\xB2", "\\xB3", "\\xB4", "\\xB5", "\\xB6", "\\xB7", "\\xB8", "\\xB9", "\\xBA", "\\xBB", "\\xBC", "\\xBD", "\\xBE", "\\xBF", "\\xC0", "\\xC1", "\\xC2", "\\xC3", "\\xC4", "\\xC5", "\\xC6", "\\xC7", "\\xC8", "\\xC9", "\\xCA", "\\xCB", "\\xCC", "\\xCD", "\\xCE", "\\xCF", "\\xD0", "\\xD1", "\\xD2", "\\xD3", "\\xD4", "\\xD5", "\\xD6", "\\xD7", "\\xD8", "\\xD9", "\\xDA", "\\xDB", "\\xDC", "\\xDD", "\\xDE", "\\xDF", "\\xE0", "\\xE1", "\\xE2", "\\xE3", "\\xE4", "\\xE5", "\\xE6", "\\xE7", "\\xE8", "\\xE9", "\\xEA", "\\xEB", "\\xEC", "\\xED", "\\xEE", "\\xEF", "\\xF0", "\\xF1", "\\xF2", "\\xF3", "\\xF4", "\\xF5", "\\xF6", "\\xF7", "\\xF8", "\\xF9", "\\xFA", "\\xFB", "\\xFC", "\\xFD", "\\xFE", "\\xFF"};
    assert_self();
    new(char, buffer, self->size * 4 + 3);
    destination = buffer;
    *destination++ = '"';
    foreach(byte, value, bytes, self);
        source = repr[value];
        length = strlen(source);
        strncpy(destination, source, length);
        destination += length;
    end_foreach(value, bytes);
    *destination++ = '"';
    *destination++ = '\0';
    resize(char, buffer, destination - buffer);
    return buffer;
}

bool bytes_bool(bytes *self)
{
    assert_self();
    return self->size > 0;
}

dword bytes_len(bytes *self)
{
    assert_self();
    return self->size;
}

bytes *bytes_deepcopy(bytes *self)
{
    assert_self();
    return bytes_from_buffer(self->size, self->data);
}

byte bytes_getitem(bytes *self, dword offset)
{
    assert_self();
    assert(offset < self->size, "Index is out of range!");
    return self->data[offset];
}

void bytes_setitem(bytes *self, dword offset, byte value)
{
    assert_self();
    assert(offset < self->size, "Index is out of range!");
    self->data[offset] = value;
}

bool bytes_find(bytes *self, byte value, dword *offset)
{
    bool found;
    assert_self();
    assert_not_null(offset);
    found = false;
    foreach(byte, current, bytes, self);
        if (current == value)
        {
            *offset = iter_key(current, bytes);
            found = true;
            iter_stop(current, bytes);
        }
    end_foreach(current, bytes);
    return found;
}

dword bytes_index(bytes *self, byte value)
{
    dword offset;
    assert(bytes_find(self, value, &offset), "Value was not found!");
    return offset;
}

void bytes_sort(bytes *self)
{
    assert_self();
    qsort(self->data, self->size, sizeof(byte), byte_cmp);
}

void bytes_rotate(bytes *self, dword offset)
{
    bytes tail;
    byte *buffer;
    assert_self();
    assert(offset < self->size, "Index is out of range!");
    tail.size = self->size - offset;
    tail.data = self->data + offset;
    if (offset > self->size >> 1)
    {
        new(byte, buffer, tail.size);
        memcpy(buffer, tail.data, tail.size);
        memmove(self->data + tail.size, self->data, offset);
        memcpy(self->data, buffer, tail.size);
    }
    else
    {
        new(byte, buffer, offset);
        memcpy(buffer, self->data, offset);
        memmove(self->data, tail.data, tail.size);
        memcpy(self->data + tail.size, buffer, offset);
    }
    del(buffer);
}

sbyte bytes_cmp(bytes *self, bytes *other)
{
    sbyte cmp;
    iter_bytes *self_iterator, *other_iterator;
    dword offset;
    assert_self();
    assert_not_null(other);
    cmp = 0;
    for (self_iterator = bytes_iter(self), other_iterator = bytes_iter(other); iter_valid(self, bytes) && iter_valid(other, bytes); iter_next(self, bytes), iter_next(other, bytes))
    {
        offset = iter_key(self, bytes);
        cmp = byte_cmp(self->data + offset, other->data + offset);
        if (cmp != 0)
            break;
    }
    if (cmp == 0)
        cmp = iter_valid(self, bytes) - iter_valid(other, bytes);
    iter_bytes_del(self_iterator);
    iter_bytes_del(other_iterator);
    return cmp;
}

bool bytes_lt(bytes *self, bytes *other)
{
    return bytes_cmp(self, other) < 0;
}

bool bytes_le(bytes *self, bytes *other)
{
    return bytes_cmp(self, other) <= 0;
}

bool bytes_eq(bytes *self, bytes *other)
{
    return bytes_cmp(self, other) == 0;
}

bool bytes_ne(bytes *self, bytes *other)
{
    return bytes_cmp(self, other) != 0;
}

bool bytes_gt(bytes *self, bytes *other)
{
    return bytes_cmp(self, other) > 0;
}

bool bytes_ge(bytes *self, bytes *other)
{
    return bytes_cmp(self, other) >= 0;
}

int byte_cmp(const void *a, const void *b)
{
    byte x, y;
    x = *(byte *)a;
    y = *(byte *)b;
    return (x > y) - (x < y);
}

iter_bytes *iter_bytes_call(bytes *data)
{
    object_call(iter_bytes, data);
}

iter_bytes *iter_bytes_new(void)
{
    object_new(iter_bytes);
}

iter_bytes *iter_bytes_copy(iter_bytes *self)
{
    object_copy(iter_bytes);
}

void iter_bytes_del(iter_bytes *self)
{
    object_del(iter_bytes);
        bytes_del(self->data);
    end_object_del();
}

void iter_bytes_init(iter_bytes *self, bytes *data)
{
    assert_not_null(data);
    self->data = bytes_copy(data);
    iter_bytes_rewind(self);
}

byte iter_bytes_current(iter_bytes *self)
{
    assert_iter(bytes);
    return self->data->data[self->offset];
}

dword iter_bytes_key(iter_bytes *self)
{
    assert_self();
    return self->offset;
}

void iter_bytes_next(iter_bytes *self)
{
    assert_self();
    self->offset += 1;
}

void iter_bytes_rewind(iter_bytes *self)
{
    assert_self();
    self->offset = 0;
}

void iter_bytes_stop(iter_bytes *self)
{
    assert_self();
    self->offset = self->data->size;
}

bool iter_bytes_valid(iter_bytes *self)
{
    assert_self();
    return self->offset < self->data->size;
}

range *range_stop(sdword stop)
{
    return range_start_stop(0, stop);
}

range *range_start_stop(sdword start, sdword stop)
{
    return range_call(start, stop, (start > stop ? -1 : +1));
}

range *range_call(sdword start, sdword stop, sdword step)
{
    object_call(range, start, stop, step);
}

range *range_new(void)
{
    object_new(range);
}

range *range_copy(range *self)
{
    object_copy(range);
}

void range_del(range *self)
{
    object_del(range);
    end_object_del();
}

void range_init(range *self, sdword start, sdword stop, sdword step)
{
    assert((start < stop && step > 0) ||
           (start > stop && step < 0) ||
           (start == stop), "Step should move start to stop!");
    self->start = start;
    self->stop = stop;
    self->step = step;
}

iter_range *iter_range_call(range *data)
{
    object_call(iter_range, data);
}

iter_range *iter_range_new(void)
{
    object_new(iter_range);
}

iter_range *iter_range_copy(iter_range *self)
{
    object_copy(iter_range);
}

void iter_range_del(iter_range *self)
{
    object_del(iter_range);
        range_del(self->data);
    end_object_del();
}

void iter_range_init(iter_range *self, range *data)
{
    assert_not_null(data);
    self->data = range_copy(data);
    self->finish = int_ceildiv(data->stop - data->start, data->step);
    iter_range_rewind(self);
}

sdword iter_range_current(iter_range *self)
{
    assert_iter(range);
    return self->data->start + self->data->step * self->offset;
}

sdword iter_range_key(iter_range *self)
{
    assert_self();
    return self->offset;
}

void iter_range_next(iter_range *self)
{
    assert_self();
    self->offset += 1;
}

void iter_range_rewind(iter_range *self)
{
    assert_self();
    self->offset = 0;
}

void iter_range_stop(iter_range *self)
{
    assert_self();
    self->offset = self->finish;
}

bool iter_range_valid(iter_range *self)
{
    assert_self();
    return self->offset < self->finish;
}

set *set_from_bytes(bytes *data)
{
    set *self;
    self = set_call();
    foreach(byte, value, bytes, data);
        self->member[value] = true;
    end_foreach(value, bytes);
    return self;
}

set *set_call(void)
{
    object_call(set);
}

set *set_new(void)
{
    object_new(set);
}

set *set_copy(set *self)
{
    object_copy(set);
}

void set_del(set *self)
{
    object_del(set);
    end_object_del();
}

void set_init(set *self)
{
    set_clear(self);
}

bool set_bool(set *self)
{
    bool nonzero;
    assert_self();
    nonzero = false;
    foreach(bool, member, set, self);
        if (member)
        {
            nonzero = true;
            iter_stop(member, set);
        }
    end_foreach(member, set);
    return nonzero;
}

word set_len(set *self)
{
    word length;
    assert_self();
    length = 0;
    foreach(bool, member, set, self);
        length += member;
    end_foreach(member, set);
    return length;
}

bool set_contains(set *self, byte elem)
{
    assert_self();
    return self->member[elem];
}

bool set_issubset(set *self, set *other)
{
    bool issubset;
    assert_not_null(other);
    issubset = true;
    foreach(bool, member, set, other);
        if (!member && self->member[iter_key(member, set)])
        {
            issubset = false;
            iter_stop(member, set);
        }
    end_foreach(member, set);
    return issubset;
}

bool set_issuperset(set *self, set *other)
{
    return set_issubset(other, self);
}

set *set_union(set *self, set *other)
{
    return set_mutate(self, other, true);
}

set *set_intersection(set *self, set *other)
{
    set *intersection;
    byte offset;
    assert_self();
    assert_not_null(other);
    intersection = set_new();
    foreach(bool, member, set, self);
        offset = iter_key(member, set);
        intersection->member[offset] = member && other->member[offset];
    end_foreach(member, set);
    return intersection;
}

set *set_difference(set *self, set *other)
{
    return set_mutate(self, other, false);
}

set *set_symmetric_difference(set *self, set *other)
{
    set *or, *and, *xor;
    assert_self();
    assert_not_null(other);
    or = set_union(self, other);
    and = set_intersection(self, other);
    xor = set_difference(or, and);
    set_del(or);
    set_del(and);
    return xor;
}

set *set_deepcopy(set *self)
{
    set *copy;
    assert_self();
    copy = set_new();
    foreach(bool, member, set, self);
        copy->member[iter_key(member, set)] = member;
    end_foreach(member, set);
    return copy;
}

void set_add(set *self, byte elem)
{
    assert_self();
    self->member[elem] = true;
}

void set_remove(set *self, byte elem)
{
    assert_self();
    assert(self->member[elem], "Element was not in set!");
    self->member[elem] = false;
}

void set_discard(set *self, byte elem)
{
    assert_self();
    self->member[elem] = false;
}

void set_clear(set *self)
{
    range *counter;
    assert_self();
    counter = range_stop(256);
    foreach(byte, offset, range, counter);
        self->member[offset] = false;
    end_foreach(offset, range);
    range_del(counter);
}

set *set_mutate(set *self, set *other, bool add)
{
    set *copy;
    assert_self();
    assert_not_null(other);
    copy = set_deepcopy(self);
    foreach(bool, member, set, other);
        if (member)
            copy->member[iter_key(member, set)] = add;
    end_foreach(member, set);
    return copy;
}

iter_set *iter_set_call(set *data)
{
    object_call(iter_set, data);
}

iter_set *iter_set_new(void)
{
    object_new(iter_set);
}

iter_set *iter_set_copy(iter_set *self)
{
    object_copy(iter_set);
}

void iter_set_del(iter_set *self)
{
    object_del(iter_set);
        set_del(self->data);
    end_object_del();
}

void iter_set_init(iter_set *self, set *data)
{
    assert_not_null(data);
    self->data = set_copy(data);
    iter_set_rewind(self);
}

bool iter_set_current(iter_set *self)
{
    assert_iter(set);
    return self->data->member[self->offset];
}

word iter_set_key(iter_set *self)
{
    assert_self();
    return self->offset;
}

void iter_set_next(iter_set *self)
{
    assert_self();
    self->offset += 1;
}

void iter_set_rewind(iter_set *self)
{
    assert_self();
    self->offset = 0;
}

void iter_set_stop(iter_set *self)
{
    assert_self();
    self->offset = 256;
}

bool iter_set_valid(iter_set *self)
{
    assert_self();
    return self->offset < 256;
}

byte iter_set_current_member(iter_set *self)
{
    return (byte)iter_set_key(self);
}

void iter_set_next_member(iter_set *self)
{
    do
        iter_set_next(self);
    while (iter_set_valid(self) && !iter_set_current(self));
}

void iter_set_rewind_member(iter_set *self)
{
    iter_set_rewind(self);
    while (iter_set_valid(self) && !iter_set_current(self))
        iter_set_next(self);
}

dict *dict_from_pairs(bytes *keys, bytes *values)
{
    dword length;
    dict *self;
    assert_not_null(keys);
    assert_not_null(values);
    length = bytes_len(keys);
    assert(bytes_len(values) == length, "Keys and values must have same length!");
    self = dict_new();
    self->keys = set_from_bytes(keys);
    assert(set_len(self->keys) == length, "Keys must contain unique bytes!");
    foreach(byte, key, bytes, keys);
        self->values[key] = bytes_getitem(values, iter_key(key, bytes));
    end_foreach(key, bytes);
    return self;
}

dict *dict_call(void)
{
    object_call(dict);
}

dict *dict_new(void)
{
    object_new(dict);
}

dict *dict_copy(dict *self)
{
    object_copy(dict);
}

void dict_del(dict *self)
{
    object_del(dict);
        set_del(self->keys);
    end_object_del();
}

void dict_init(dict *self)
{
    self->keys = set_call();
}

bool dict_bool(dict *self)
{
    assert_self();
    return set_bool(self->keys);
}

word dict_len(dict *self)
{
    assert_self();
    return set_len(self->keys);
}

bool dict_contains(dict *self, byte key)
{
    assert_self();
    return set_contains(self->keys, key);
}

byte dict_getitem(dict *self, byte key)
{
    assert_self();
    assert(set_contains(self->keys, key), "Key is not in dictionary!");
    return self->values[key];
}

void dict_setitem(dict *self, byte key, byte value)
{
    assert_self();
    set_add(self->keys, key);
    self->values[key] = value;
}

void dict_delitem(dict *self, byte key)
{
    assert_self();
    assert(set_contains(self->keys, key), "Key is not in dictionary!");
    set_discard(self->keys, key);
}

bytes *dict_keys(dict *self)
{
    assert_self();
    return bytes_from_set(self->keys);
}

bytes *dict_values(dict *self)
{
    bytes *values;
    byte offset;
    assert_self();
    values = bytes_call(set_len(self->keys));
    offset = 0;
    foreach(byte, value, dict, self);
        bytes_setitem(values, offset++, value);
    end_foreach(value, dict);
    return values;
}

dict *dict_reversed(dict *self)
{
    dict *reversed;
    assert_self();
    reversed = dict_call();
    foreach(byte, value, dict, self);
        if (set_contains(reversed->keys, value))
        {
            dict_del(reversed);
            reversed = NULL;
            iter_stop(value, dict);
        }
        else
            dict_setitem(reversed, value, iter_key(value, dict));
    end_foreach(value, dict);
    return reversed;
}

iter_dict *iter_dict_call(dict *data)
{
    object_call(iter_dict, data);
}

iter_dict *iter_dict_new(void)
{
    object_new(iter_dict);
}

iter_dict *iter_dict_copy(iter_dict *self)
{
    object_copy(iter_dict);
}

void iter_dict_del(iter_dict *self)
{
    object_del(iter_dict);
        dict_del(self->data);
        iter_set_del(self->iter);
    end_object_del();
}

void iter_dict_init(iter_dict *self, dict *data)
{
    assert_not_null(data);
    self->data = dict_copy(data);
    self->iter = set_iter(data->keys);
    iter_dict_rewind(self);
}

byte iter_dict_current(iter_dict *self)
{
    assert_iter(dict);
    return self->data->values[iter_set_current_member(self->iter)];
}

byte iter_dict_key(iter_dict *self)
{
    assert_self();
    return iter_set_current_member(self->iter);
}

void iter_dict_next(iter_dict *self)
{
    assert_self();
    iter_set_next_member(self->iter);
}

void iter_dict_rewind(iter_dict *self)
{
    assert_self();
    iter_set_rewind_member(self->iter);
}

void iter_dict_stop(iter_dict *self)
{
    assert_self();
    iter_set_stop(self->iter);
}

bool iter_dict_valid(iter_dict *self)
{
    assert_self();
    return iter_set_valid(self->iter);
}

list *list_call(dword size)
{
    object_call(list, size);
}

list *list_new(void)
{
    object_new(list);
}

list *list_copy(list *self)
{
    object_copy(list);
}

void list_del(list *self)
{
    object_del(list);
        del(self->data);
    end_object_del();
}

void list_init(list *self, dword size)
{
    self->size = size;
    new(void *, self->data, size);
    zero(void *, self->data, size);
}

bool list_bool(list *self)
{
    assert_self();
    return self->size > 0;
}

dword list_len(list *self)
{
    assert_self();
    return self->size;
}

void *list_getitem(list *self, dword offset)
{
    assert_self();
    assert(offset < self->size, "Index is out of range!");
    return self->data[offset];
}

void list_setitem(list *self, dword offset, void *value)
{
    assert_self();
    assert(offset < self->size, "Index is out of range!");
    self->data[offset] = value;
}

iter_list *iter_list_call(list *data)
{
    object_call(iter_list, data);
}

iter_list *iter_list_new(void)
{
    object_new(iter_list);
}

iter_list *iter_list_copy(iter_list *self)
{
    object_copy(iter_list);
}

void iter_list_del(iter_list *self)
{
    object_del(iter_list);
        list_del(self->data);
    end_object_del();
}

void iter_list_init(iter_list *self, list *data)
{
    assert_not_null(data);
    self->data = list_copy(data);
    iter_list_rewind(self);
}

void *iter_list_current(iter_list *self)
{
    assert_iter(list);
    return self->data->data[self->offset];
}

dword iter_list_key(iter_list *self)
{
    assert_self();
    return self->offset;
}

void iter_list_next(iter_list *self)
{
    assert_self();
    self->offset += 1;
}

void iter_list_rewind(iter_list *self)
{
    assert_self();
    self->offset = 0;
}

void iter_list_stop(iter_list *self)
{
    assert_self();
    self->offset = self->data->size;
}

bool iter_list_valid(iter_list *self)
{
    assert_self();
    return self->offset < self->data->size;
}

deque *deque_call(bytes *buffer)
{
    object_call(deque, buffer);
}

deque *deque_new(void)
{
    object_new(deque);
}

deque *deque_copy(deque *self)
{
    object_copy(deque);
}

void deque_del(deque *self)
{
    object_del(deque);
        bytes_del(self->buffer);
    end_object_del();
}

void deque_init(deque *self, bytes *buffer)
{
    assert_not_null(buffer);
    self->buffer = bytes_copy(buffer);
    self->offset = 0;
}

bool deque_bool(deque *self)
{
    assert_self();
    return bytes_bool(self->buffer);
}

dword deque_len(deque *self)
{
    assert_self();
    return bytes_len(self->buffer);
}

void deque_append(deque *self, byte value)
{
    assert_self();
    if (bytes_bool(self->buffer))
    {
        bytes_setitem(self->buffer, self->offset++, value);
        self->offset %= bytes_len(self->buffer);
    }
}

iter_deque *iter_deque_call(deque *data)
{
    object_call(iter_deque, data);
}

iter_deque *iter_deque_new(void)
{
    object_new(iter_deque);
}

iter_deque *iter_deque_copy(iter_deque *self)
{
    object_copy(iter_deque);
}

void iter_deque_del(iter_deque *self)
{
    object_del(iter_deque);
        deque_del(self->data);
    end_object_del();
}

void iter_deque_init(iter_deque *self, deque *data)
{
    assert_not_null(data);
    self->data = deque_copy(data);
    iter_deque_rewind(self);
}

byte iter_deque_current(iter_deque *self)
{
    assert_iter(deque);
    return bytes_getitem(self->data->buffer, (self->data->offset + self->offset) % bytes_len(self->data->buffer));
}

dword iter_deque_key(iter_deque *self)
{
    assert_self();
    return self->offset;
}

void iter_deque_next(iter_deque *self)
{
    assert_self();
    self->offset += 1;
}

void iter_deque_rewind(iter_deque *self)
{
    assert_self();
    self->offset = 0;
}

void iter_deque_stop(iter_deque *self)
{
    assert_self();
    self->offset = bytes_len(self->data->buffer);
}

bool iter_deque_valid(iter_deque *self)
{
    return self->offset < bytes_len(self->data->buffer);
}

sdword int_ceildiv(sdword dividend, sdword divisor)
{
    ldiv_t divmod;
    divmod = ldiv(dividend, divisor);
    return divmod.quot + (divmod.rem > 0);
}

byte int_bit_length(dword number)
{
    byte length;
    length = 0;
    while (number > 0)
    {
        length += 1;
        number >>= 1;
    }
    return length;
}

sdword int_mod(sdword dividend, sdword divisor)
{
    return (dividend % divisor + divisor) % divisor;
}

#if defined(__WIN32) || defined (__WINNT)
#include <windows.h>
#include <wincrypt.h>
typedef BOOL (WINAPI *CRYPTACQUIRECONTEXTA)\
        (HCRYPTPROV *phProv, LPCSTR pszContainer, LPCSTR pszProvider, DWORD dwProvType, DWORD dwFlags);
typedef BOOL (WINAPI *CRYPTGENRANDOM)\
        (HCRYPTPROV hProv, DWORD dwLen,  BYTE *pbBuffer);

static CRYPTGENRANDOM pCryptGenRandom = NULL;
static HCRYPTPROV hCryptProv = 0;

void random_bytes(bytes *buffer)
{
    HINSTANCE hAdvAPI32;
    CRYPTACQUIRECONTEXTA pCryptAcquireContext;
    assert_not_null(buffer);
    if (hCryptProv == 0)
    {
        hAdvAPI32 = GetModuleHandle("advapi32.dll");
        assert_not_null(hAdvAPI32);
        pCryptAcquireContext = (CRYPTACQUIRECONTEXTA)GetProcAddress(hAdvAPI32, "CryptAcquireContextA");
        assert_not_null(pCryptAcquireContext);
        pCryptGenRandom = (CRYPTGENRANDOM)GetProcAddress(hAdvAPI32, "CryptGenRandom");
        assert_not_null(pCryptGenRandom);
        assert(pCryptAcquireContext(&hCryptProv, NULL, NULL, PROV_RSA_FULL, CRYPT_VERIFYCONTEXT), "Failed to initialize Windows random API (CryptoGen)");
    }
    assert(pCryptGenRandom(hCryptProv, buffer->size, buffer->data), "Failed to fill buffer using CryptoGen");
}
#elif defined(__VMS)
#include <openssl/rand.h>
void random_bytes(bytes *buffer)
{
    assert_not_null(buffer);
    assert(RAND_pseudo_bytes(buffer->data, buffer->size) >= 0, "Failed to fill buffer using RAND_pseudo_bytes");
}
#else
#include <fcntl.h>
void random_bytes(bytes *buffer)
{
    int file, count;
    byte *memory;
    dword size;
    assert_not_null(buffer);
    memory = buffer->data;
    size = buffer->size;
    file = open("/dev/urandom", O_RDONLY);
    assert(file >= 0, "Failed to open /dev/urandom");
    while (size > 0)
    {
        do
            count = read(file, memory, size);
        while (count < 0 && errno == EINTR);
        assert(count > 0, "Failed to read bytes from /dev/urandom");
        memory += (dword)count;
        size -= (dword)count;
    }
    close(file);
}
#endif

dword random_range(dword stop)
{
    byte bits;
    bytes *buffer;
    dword mask, number;
    if (stop < 2)
        return 0;
    bits = int_bit_length(stop - 1);
    buffer = bytes_call(int_ceildiv(bits, 8));
    mask = (1 << bits) - 1;
    do
    {
        random_bytes(buffer);
        number = 0;
        foreach(byte, value, bytes, buffer);
            number = (number << 8) + value;
        end_foreach(value, bytes);
        number &= mask;
    }
    while (number >= stop);
    bytes_del(buffer);
    return number;
}

byte random_choice(bytes *buffer)
{
    assert_not_null(buffer);
    return bytes_getitem(buffer, random_range(bytes_len(buffer)));
}

void random_shuffle(bytes *buffer)
{
    dword range, offset, choice;
    assert_not_null(buffer);
    range = bytes_len(buffer);
    if (range > 2)
    {
        range -= 1;
        foreach(byte, value, bytes, buffer);
            offset = iter_key(value, bytes);
            choice = random_range(range);
            if (choice >= offset)
                choice += 1;
            bytes_setitem(buffer, offset, bytes_getitem(buffer, choice));
            bytes_setitem(buffer, choice, value);
        end_foreach(value, bytes);
    }
}

/* Return a Key instance created from bytes_used and chain_size.
 * 
 * Creating a new key is easy with this method. Call this class method
 * with the bytes you want the key to recognize along with the size of
 * the chains you want the encryption/decryption processes to use.
 */

Key *Key_create(bytes *bytes_used, word chain_size)
{
    set *group;
    bytes *selection;
    list *blocks;
    range *counter;
    Key *new_key;
    assert_not_null(bytes_used);
    group = set_from_bytes(bytes_used);
    selection = bytes_from_set(group);
    set_del(group);
    blocks = list_call(chain_size);
    counter = range_stop(chain_size);
    foreach(word, offset, range, counter);
        random_shuffle(selection);
        list_setitem(blocks, offset, bytes_deepcopy(selection));
    end_foreach(offset, range);
    range_del(counter);
    bytes_del(selection);
    new_key = Key_call(blocks);
    list_del(blocks);
    return new_key;
}

Key *Key_call(list *data)
{
    object_call(Key, data);
}

Key *Key_new(void)
{
    object_new(Key);
}

Key *Key_copy(Key *self)
{
    object_copy(Key);
}

void Key_del(Key *self)
{
    object_del(Key);
        foreach(bytes *, block, list, self->data);
            bytes_del(block);
        end_foreach(block, list);
        list_del(self->data);
        bytes_del(self->base);
        bytes_del(self->encoder);
        foreach(bytes *, table, list, self->axes);
            bytes_del(table);
        end_foreach(table, list);
        list_del(self->axes);
        bytes_del(self->order);
        foreach(bytes *, table, list, self->decoder);
            bytes_del(table);
        end_foreach(table, list);
        list_del(self->decoder);
    end_object_del();
}

/* Initialize the Key instance's variables after testing the data.
 * 
 * Keys are created with tuples of carefully constructed bytes arrays.
 * This method tests the given data before going on to build internal
 * tables for efficient encoding and decoding methods later on.
 */

void Key_init(Key *self, list *data)
{
    Key_test_data(data);
    Key_make_vars(self, data);
}

/* Test the data for correctness in its construction.
 * 
 * The data must be a tuple of at least two byte arrays. Each byte
 * array must have at least two bytes, all of which must be unique.
 * Furthermore, all arrays should share the exact same byte set.
 */

void Key_test_data(list *data)
{
    dword list_size, bytes_size, next_size;
    bytes *item;
    set *group, *next_group, *sym_diff;
    range *counter;
    assert_not_null(data);
    list_size = list_len(data);
    assert(list_size > 1, "Data must contain more than one item!");
    item = list_getitem(data, 0);
    bytes_size = bytes_len(item);
    assert(bytes_size > 1, "Data must contain more than one byte!");
    group = set_from_bytes(item);
    assert(set_len(group) == bytes_size, "Items must contain unique bytes!");
    counter = range_start_stop(1, list_size);
    foreach(word, offset, range, counter);
        item = list_getitem(data, offset);
        next_size = bytes_len(item);
        assert(next_size == bytes_size, "All items must have the same size!");
        next_group = set_from_bytes(item);
        assert(set_len(next_group) == next_size, "Items must contain unique bytes!");
        sym_diff = set_symmetric_difference(next_group, group);
        set_del(next_group);
        assert(!set_bool(sym_diff), "All items must use the same bytes!");
        set_del(sym_diff);
    end_foreach(offset, range);
    range_del(counter);
    set_del(group);
}

/* Build various internal tables for optimized calculations.
 * 
 * Encoding and decoding rely on complex relationships with the given
 * data. This method caches several of these key relationships for use
 * when the encryption and decryption processes are being executed.
 */

void Key_make_vars(Key *self, list *data)
{
    word prefix_len, size;
    bytes *base, *order;
    byte offset;
    self->data = list_copy(data);
    self->prefix_len = prefix_len = list_len(data) - 1;
    self->base = base = bytes_copy(list_getitem(data, 0));
    self->size = size = bytes_len(base);
    offset = Key_calculate_offset(data, prefix_len, base, size);
    self->encoder = bytes_deepcopy(base);
    bytes_rotate(self->encoder, offset);
    self->axes = Key_calculate_axes(data, prefix_len, base, size);
    self->order = order = bytes_deepcopy(base);
    bytes_sort(order);
    self->decoder = Key_calculate_decoder(base, size, offset, order);
}

byte Key_calculate_offset(list *data, word prefix_len, bytes *base, word size)
{
    dword sum;
    range *counter;
    sum = 0;
    counter = range_start_stop(1, prefix_len);
    foreach(word, offset, range, counter);
        sum += bytes_index(base, bytes_getitem(list_getitem(data, offset), 0));
    end_foreach(offset, range);
    range_del(counter);
    return int_mod(-sum, size);
}

list *Key_calculate_axes(list *data, word prefix_len, bytes *base, word size)
{
    list *axes;
    range *counter;
    bytes *block, *table;
    axes = list_call(prefix_len);
    counter = range_start_stop(prefix_len, 0);
    foreach(word, offset, range, counter);
        block = list_getitem(data, offset);
        table = bytes_call(size);
        foreach(byte, value, bytes, block);
            bytes_setitem(table, iter_key(value, bytes), bytes_index(base, value));
        end_foreach(value, bytes);
        list_setitem(axes, iter_key(offset, range), table);
    end_foreach(offset, range);
    range_del(counter);
    return axes;
}

list *Key_calculate_decoder(bytes *base, word size, byte offset, bytes *order)
{
    list *grid;
    range *counter;
    bytes *row;
    grid = list_call(size);
    counter = range_stop(size);
    foreach(byte, rotation, range, counter);
        row = bytes_call(size);
        foreach(byte, value, bytes, order);
            bytes_setitem(row, bytes_index(order, bytes_getitem(base, (rotation + iter_key(value, bytes)) % size)), value);
        end_foreach(value, bytes);
        list_setitem(grid, (rotation + offset) % size, row);
    end_foreach(rotation, range);
    range_del(counter);
    return grid;
}

/* Raise an error if the primer is not compatible with this key.
 * 
 * Key and primers have a certain relationship that must be maintained
 * in order for them to work together. Since the primer understands
 * the requirements, it is asked to check this key for compatibility.
 */

void Key_test_primer(Key *self, Primer *vector)
{
    Primer_test_key(vector, self);
}

/* Encode index based on internal tables and return byte code.
 * 
 * An index probes into the various axes of the multidimensional,
 * virtual grid that a key represents. The index is evaluated, and
 * the value at its coordinates is returned by running this method.
 */

byte Key_encode(Key *self, deque *prefix, byte current)
{
    return bytes_getitem(self->encoder, (Key_calculate_sum(self, prefix) + current) % self->size);
}

/* Decode index based on internal tables and return byte code.
 * 
 * Decoding does the exact same thing as encoding, but it indexes
 * into a virtual grid that represents the inverse of the encoding
 * grid. Tables are used to make the process fast and efficient.
 */

byte Key_decode(Key *self, deque *prefix, byte current)
{
    return bytes_getitem(list_getitem(self->decoder, Key_calculate_sum(self, prefix) % self->size), current);
}

dword Key_calculate_sum(Key *self, deque *prefix)
{
    dword sum;
    assert_self();
    assert_not_null(prefix);
    assert(deque_len(prefix) == self->prefix_len, "Prefix size conflicts with key dimensions!");
    sum = 0;
    foreach(byte, probe, deque, prefix);
        sum += bytes_getitem(list_getitem(self->axes, iter_key(probe, deque)), probe);
    end_foreach(probe, deque);
    return sum;
}

/* Data that the instance was initialized with.
 * 
 * This is the tuple of byte arrays used to create this key and can
 * be used to create an exact copy of this key at some later time.
 */

list *Key_get_data(Key *self)
{
    assert_self();
    return self->data;
}

/* Dimensions that the internal, virtual grid contains.
 * 
 * The virtual grid has a number of axes that can be referenced when
 * indexing into it, and this number is the count of its dimensions.
 */

word Key_get_prefix_len(Key *self)
{
    assert_self();
    return self->prefix_len;
}

/* Base value that the internal grid is built from.
 * 
 * The Sudoku nature of the grid comes from rotating this value by
 * offsets, keeping values unique along any axis while traveling.
 */

bytes *Key_get_base(Key *self)
{
    assert_self();
    return self->base;
}

/* Order of base after its values have been sorted.
 * 
 * A sorted base is important when constructing inverse rows and when
 * encoding raw bytes for use in updating an encode/decode index.
 */

bytes *Key_get_order(Key *self)
{
    assert_self();
    return self->order;
}

/* Return a Primer instance from a parent Key.
 * 
 * Primers must be compatible with the keys they are used with. This
 * method takes a key and constructs a cryptographically sound primer
 * that is ready to use in the beginning stages of encryption.
 */

Primer *Primer_create(Key *primary)
{
    bytes *base, *data;
    word prefix_len;
    range *counter;
    Primer *new_primer;
    base = Key_get_base(primary);
    prefix_len = Key_get_prefix_len(primary);
    data = bytes_call(prefix_len);
    counter = range_stop(prefix_len);
    foreach(word, offset, range, counter);
        bytes_setitem(data, offset, random_choice(base));
    end_foreach(offset, range);
    range_del(counter);
    new_primer = Primer_call(data);
    bytes_del(data);
    return new_primer;
}

Primer *Primer_call(bytes *data)
{
    object_call(Primer, data);
}

Primer *Primer_new(void)
{
    object_new(Primer);
}

Primer *Primer_copy(Primer *self)
{
    object_copy(Primer);
}

void Primer_del(Primer *self)
{
    object_del(Primer);
        bytes_del(self->data);
    end_object_del();
}

/* Initialize the Primer instance after testing validity of data.
 * 
 * Though not as complicated in its requirements as keys, primers do
 * need some simple structure in the data they are given. A checking
 * method is run before saving the data to the instance's attribute.
 */

void Primer_init(Primer *self, bytes *data)
{
    Primer_test_data(data);
    self->data = bytes_copy(data);
}

/* Test the data for correctness and test the data.
 * 
 * In order for the primer to be compatible with the nature of the
 * Markov Encryption processes, the data must be an array of bytes;
 * and to act as a primer, it must contain at least some information.
 */

void Primer_test_data(bytes *data)
{
    assert_not_null(data);
    assert(bytes_bool(data), "Data must not be empty!");
}

/* Raise an error if the key is not compatible with this primer.
 * 
 * Primers provide needed data to start encryption and decryption. For
 * it be compatible with a key, it must contain one byte less than the
 * key's dimensions and must be a subset of the base in the key.
 */

void Primer_test_key(Primer *self, Key *primary)
{
    set *data, *base;
    assert_self();
    assert_not_null(primary);
    assert(bytes_len(self->data) == Key_get_prefix_len(primary), "Key size must be one more than primer size!");
    data = set_from_bytes(self->data);
    base = set_from_bytes(Key_get_base(primary));
    assert(set_issubset(data, base), "Primer data must be a subset of key data!");
    set_del(data);
    set_del(base);
}

/* Data that the instance was initialized with.
 * 
 * This is the byte array used to create this primer and can be used
 * if desired to create an copy of this primer at some later time.
 */

bytes *Primer_get_data(Primer *self)
{
    assert_self();
    return self->data;
}

_Processor *_Processor_call(Key *primary, Primer *vector)
{
    object_call(_Processor, primary, vector);
}

_Processor *_Processor_new(void)
{
    object_new(_Processor);
}

_Processor *_Processor_copy(_Processor *self)
{
    object_copy(_Processor);
}

void _Processor_del(_Processor *self)
{
    object_del(_Processor);
        Key_del(self->primary);
        dict_del(self->encoder);
        deque_del(self->prefix);
        bytes_del(self->decoder);
    end_object_del();
}

/* Initialize the _Processor instance if it is from a child class.
 * 
 * After passing several tests for creating a valid processing object,
 * the key is saved, and the primer is used to start an index. Tables
 * are also formed for converting byte values between systems.
 */

void _Processor_init(_Processor *self, Key *primary, Primer *vector)
{
    bytes *prefix;
    dict *reversed;
    assert_not_null(primary);
    assert_not_null(vector);
    Key_test_primer(primary, vector);
    self->primary = Key_copy(primary);
    self->encoder = dict_call();
    foreach(byte, value, bytes, Key_get_order(primary));
        dict_setitem(self->encoder, value, iter_key(value, bytes));
    end_foreach(value, bytes);
    prefix = bytes_call(Key_get_prefix_len(primary));
    foreach(byte, value, bytes, Primer_get_data(vector));
        bytes_setitem(prefix, iter_key(value, bytes), dict_getitem(self->encoder, value));
    end_foreach(value, bytes);
    self->prefix = deque_call(prefix);
    bytes_del(prefix);
    reversed = dict_reversed(self->encoder);
    self->decoder = dict_values(reversed);
    dict_del(reversed);
}

/* Process the data and return its transformed state.
 * 
 * A cache for the data transformation is created and an internal
 * method is run to quickly encode or decode the given bytes. The
 * cache is finally converted to immutable bytes when returned.
 */

bytes *_Processor_process(_Processor *self, bytes *data, void (*converter)(dict *encoder, byte value, Key *primary, deque *prefix, bytes *cache, dword offset))
{
    bytes *cache;
    assert_self();
    assert_not_null(data);
    assert_not_null(converter);
    cache = bytes_call(bytes_len(data));
    foreach(byte, value, bytes, data);
        if (dict_contains(self->encoder, value))
            converter(self->encoder, value, self->primary, self->prefix, cache, iter_key(value, bytes));
        else
            bytes_setitem(cache, iter_key(value, bytes), value);
    end_foreach(value, bytes);
    return cache;
}

/* Primer representing the state of the internal index.
 * 
 * The index can be retrieved as a primer, useful for initializing
 * another processor in the same starting state as the current one.
 */

Primer *_Processor_get_primer(_Processor *self)
{
    bytes *data;
    Primer *new_primer;
    assert_self();
    data = bytes_call(deque_len(self->prefix));
    foreach(byte, value, deque, self->prefix);
        bytes_setitem(data, iter_key(value, deque), bytes_getitem(self->decoder, value));
    end_foreach(value, deque);
    new_primer = Primer_call(data);
    bytes_del(data);
    return new_primer;
}

/* Encrypt the data with the given arguments.
 * 
 * To run the encryption process as fast as possible, methods are
 * cached as names. As the algorithm operates, only recognized bytes
 * are encoded while running through the selective processing loop.
 */

bytes *Encrypter_process(Encrypter *self, bytes *data)
{
    return _Processor_process(self, data, Encrypter_convert);
}

void Encrypter_convert(dict *encoder, byte value, Key *primary, deque *prefix, bytes *cache, dword offset)
{
    byte code;
    code = dict_getitem(encoder, value);
    bytes_setitem(cache, offset, Key_encode(primary, prefix, code));
    deque_append(prefix, code);
}

/* Decrypt the data with the given arguments.
 * 
 * To run the decryption process as fast as possible, methods are
 * cached as names. As the algorithm operates, only recognized bytes
 * are decoded while running through the selective processing loop.
 */

bytes *Decrypter_process(Decrypter *self, bytes *data)
{
    return _Processor_process(self, data, Decrypter_convert);
}

void Decrypter_convert(dict *encoder, byte value, Key *primary, deque *prefix, bytes *cache, dword offset)
{
    byte code;
    code = Key_decode(primary, prefix, dict_getitem(encoder, value));
    bytes_setitem(cache, offset, code);
    deque_append(prefix, dict_getitem(encoder, code));
}