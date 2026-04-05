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

  int dayOfWeek = 7;

  switch (dayOfWeek) {
  case 1:
    printf("It is Monday");
    break;
  case 2:
    printf("It is Tuesday");
    break;
  case 3:
    printf("It is Wednesday");
    break;
  case 4:
    printf("It is Thursday");
    break;
  case 5:
    printf("It is Friday");
    break;
  case 6:
    printf("It is Saturday");
    break;
  case 7:
    printf("It is Sunday");
    break;
  default:
    printf("Please enter a number (1-7)");
  }

  return 0;
}
