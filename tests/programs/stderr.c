#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/stat.h>

int main(int argc, char **argv)
{
    fprintf(stderr, "---- stderr test ----\n");
    for (int i = 0; i < 10; i++) fprintf(stderr, "%d\n", i);
    return 0;
}
