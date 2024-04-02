#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/stat.h>

int main(int argc, char **argv, char **envp)
{
    printf("---- env test ----\n"); // print all environment variables
    for (int i = 0; envp[i] != NULL; i++) {
        printf("%s\n", envp[i]);
        fflush(stdout);
    }
    return 0;
}