#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int main() {

  bool play = true;

  printf("Welcome to my first real program in C: Rock, Paper, Scissors!\n\n");

  while (play) {

    srand(time(0));
    int input;

    char pos[3][8] = {"Rock", "Paper", "Scissors"};

    int comp_choice = rand() % 3;

    for (int i = 0; i < 3; i++)
      printf("\n\n%s - [%d] ", pos[i], i);

    //   printf("%d", comp_choice);         THIS WAS FOR TESTING THE RANDOM
    //   NUMBER
    while (1) {
      printf("\n\nEnter a choice: ");
      if (scanf(" %d", &input) == 1) {
        if (input >= 0 && input <= 2) {
          break;
        }
      }
      while (getchar() != '\n')
        ;
      printf("Invalid input. Please enter 0, 1, or 2.\n");
    }

    printf("\nComputer's choice is:%s", pos[comp_choice]);

    printf("\n\nYour choice is:%s\n\n\n", pos[input]);

    if ((input == 0 && comp_choice == 0) || (input == 1 && comp_choice == 1) ||
        (input == 2 && comp_choice == 2)) {
      printf("Tie");
    } else if ((input == 0 && comp_choice == 1) ||
               (input == 1 && comp_choice == 2) ||
               (input == 2 && comp_choice == 0)) {
      printf("You Lost :(");
    } else if ((input == 0 && comp_choice == 2) ||
               (input == 1 && comp_choice == 0) ||
               (input == 2 && comp_choice == 1)) {
      printf("You won :)");
    }

    int play_choice;

    while (1) {
      printf("\n\nWould you like to play again?\n\nNo - [0] | Yes - "
             "[1]\n\nChoice: ");
      if (scanf(" %d", &play_choice) == 1) {
        if (play_choice >= 0 && play_choice <= 1) {
          break;
        }
      }

      while (getchar() != '\n')
        ;
      printf("Invalid input. Please enter 0 or 1\n");
    }

    play = (play_choice == 1);
    if (play == 0) {
      printf("\n\nGoodbye!\n\n\n");
    }
  }

  return 0;
}
