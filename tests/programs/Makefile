BLU			= \033[0;34m
GRN			= \033[0;32m
RED			= \033[0;31m
RST			= \033[0m
END			= \e[0m

SRCS		= $(wildcard ./*.c)
OBJS_DIR	= ./
OBJS		= $(SRCS:.c=.out)
OBJECTS_PREFIXED = $(addprefix $(OBJS_DIR), $(OBJS))
CC			= gcc
CC_FLAGS	= # -Wall -Werror -Wextra

$(OBJS_DIR)%.out : %.c
	@$(CC) $(CC_FLAGS) $< -o $@
	@@printf "\033[2K\r\033[0;32m[END]\033[0m '$<'$(END)\n"


all: $(OBJECTS_PREFIXED)

clean:
	@rm -rf ./*.out
	@printf "\033[2K\r${GRN}[CLEAN]${RST} done$(END)"

fclean: clean

re: fclean all

.PHONY:		all clean re