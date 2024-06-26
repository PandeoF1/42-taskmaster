#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <signal.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>

void sigusr1_handler(int signo) {
	printf("Received SIGUSR1 signal!\n");
	fflush(stdout);
}

int main(int argc, char **argv)
{
	printf("---- sigkill test ----\n");
	signal(SIGUSR1, sigusr1_handler);
	int count = 0;
	while (1) {
		printf("Waiting for SIGUSR1 signal... %d %ds\n", getpid(), count);
		count += 1;
		sleep(1);
		fflush(stdout);
	}
	return 0;
}