/*
 * =====================================================================================
 *
 *       Filename:  switch.c
 *
 *    Description:  Practicing with switches
 *
 *        Version:  1.0
 *        Created:  04/04/2026 09:29:41 PM
 *       Revision:  none
 *       Compiler:  gcc
 *
 *      Author(s):  BransonBailey (Branson Bailey),
 *   Organization:
 *
 * =====================================================================================
 */
#include <stdio.h>
#include <stdlib.h>

int main() {

  int dayOfWeek = 0;

  printf("Enter the day of the week (1-7): ");
  scanf("%d", &dayOfWeek);

  switch (dayOfWeek) {
  case 1:
    printf("\nIt is Monday");
    break;
  case 2:
    printf("\nIt is Tuesday");
    break;
  case 3:
    printf("\nIt is Wednesday");
    break;
  case 4:
    printf("\nIn is Thursday");
    break;
  case 5:
    printf("\nInt is Friday");
    break;
  case 6:
    printf("\nIt is Saturday");
    break;
  case 7:
    printf("\nIt is Sunday");
    break;
  default:
    printf("\nPlease enter a number (1-7)");
  }

  return 0;
}
