/*
 * =====================================================================================
 *
 *       Filename:  hangman.c
 *
 *    Description: A hangman game!
 *
 *        Version:  1.0
 *        Created:  03/30/2026 12:31:02 PM
 *       Revision:  none
 *       Compiler:  gcc
 *
 *         Author:  Branson
 *   Organization:
 *
 * =====================================================================================
 */
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

int count_lines(const char *filename) {
  FILE *file = fopen(filename, "r");
  if (!file)
    return 0;

  int count = 0;
  char ch;
  while ((ch = fgetc(file)) != EOF) {
    if (ch == '\n')
      count++;
  }
  fclose(file);
  return count > 0 ? count : 0;
}

int main() {
  bool play = true;

  printf("Welcome to Hangman!!\n\n\n");

  while (play) {
    srand(time(0));
    const char *filename = "hangman_wordlist.txt";
    int line_count = count_lines(filename);

    if (line_count <= 0) {
      printf("Word list is empty or couldn't be read\n");
      break;
    }

    int word_line = rand() % line_count;

    FILE *file;
    char line[256];

    file = fopen("hangman_wordlist.txt", "r");

    if (file == NULL) {
      printf("Unable to open file.\n");
      break;
    }

    int current_line = 0;
    while (fgets(line, sizeof(line), file)) {
      line[strcspn(line, "\n")] = 0;

      // printf("Length of line: %lu\n", strlen(line));

      if (current_line == word_line) {

        for (int i = 0; i < strlen(line); i++) {
          printf(" _");
        }
        printf("\n");
        break;
      }
      current_line++;
    }

    fclose(file);
    printf("\n");

    int play_input;
    printf("Play again? (1 for yes, 0 for no): ");
    scanf("%d", &play_input);
    play = play_input != 0;
  }

  return 0;
}
