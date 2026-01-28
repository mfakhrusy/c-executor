// threads_single.c
// Combined version of: common.h + common_threads.h + threads.c
// this is not my code, credit to the OS: Three Easy Pieces book by remzi-arpacidusseau
// https://github.com/remzi-arpacidusseau/ostep-code/blob/master/intro/threads.c

#include <stdio.h>
#include <stdlib.h>

#include <sys/time.h>
#include <sys/stat.h>
#include <assert.h>

#include <pthread.h>
#include <sched.h>

#ifdef __linux__
#include <semaphore.h>
#endif

// ======================
// common.h (merged)
// ======================

double GetTime() {
    struct timeval t;
    int rc = gettimeofday(&t, NULL);
    assert(rc == 0);
    return (double)t.tv_sec + (double)t.tv_usec / 1e6;
}

void Spin(int howlong) {
    double t = GetTime();
    while ((GetTime() - t) < (double)howlong)
        ; // do nothing in loop
}

// ======================
// common_threads.h (merged)
// ======================

#define Pthread_create(thread, attr, start_routine, arg) \
    assert(pthread_create(thread, attr, start_routine, arg) == 0)

#define Pthread_join(thread, value_ptr) \
    assert(pthread_join(thread, value_ptr) == 0)

#define Pthread_mutex_lock(m) assert(pthread_mutex_lock(m) == 0)
#define Pthread_mutex_unlock(m) assert(pthread_mutex_unlock(m) == 0)
#define Pthread_cond_signal(cond) assert(pthread_cond_signal(cond) == 0)
#define Pthread_cond_wait(cond, mutex) assert(pthread_cond_wait(cond, mutex) == 0)

#define Mutex_init(m) assert(pthread_mutex_init(m, NULL) == 0)
#define Mutex_lock(m) assert(pthread_mutex_lock(m) == 0)
#define Mutex_unlock(m) assert(pthread_mutex_unlock(m) == 0)
#define Cond_init(cond) assert(pthread_cond_init(cond, NULL) == 0)
#define Cond_signal(cond) assert(pthread_cond_signal(cond) == 0)
#define Cond_wait(cond, mutex) assert(pthread_cond_wait(cond, mutex) == 0)

#ifdef __linux__
#define Sem_init(sem, value) assert(sem_init(sem, 0, value) == 0)
#define Sem_wait(sem) assert(sem_wait(sem) == 0)
#define Sem_post(sem) assert(sem_post(sem) == 0)
#endif

// ======================
// threads.c (original program)
// ======================

volatile int counter = 0;
int loops;

void *worker(void *arg) {
    for (int i = 0; i < loops; i++) {
        counter++;
    }
    return NULL;
}

int main(void) {
    loops = 1000;                 // default number of increments per thread
    int num_threads = 1000;       // default number of threads

    pthread_t threads[1000];

    printf("Initial value : %d\n", counter);

    // create 1000 threads
    for (int i = 0; i < num_threads; i++) {
        Pthread_create(&threads[i], NULL, worker, NULL);
    }

    // join 1000 threads
    for (int i = 0; i < num_threads; i++) {
        Pthread_join(threads[i], NULL);
    }

    printf("Final value   : %d\n", counter);

    return 0;
}
