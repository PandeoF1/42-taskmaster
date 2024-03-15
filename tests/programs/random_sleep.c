#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#include <time.h>
#include <sys/time.h>

int main(int argc, char **argv)
{
    int max_sleep = atoi(argv[1]);
    printf("---- random sleep ----\n");
    struct timeval tv;
    gettimeofday(&tv, NULL);
    srand(tv.tv_usec);
    int random = rand() % max_sleep;
    printf("pid: %d sleep: %d\n", getpid(), random);
    sleep(random);
    return 0;
}