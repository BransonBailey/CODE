/*
 * =====================================================================================
 *
 *       Filename:  swapping_numbers_without_temp.c
 *
 *    Description:
 *
 *        Version:  1.0
 *        Created:  04/06/2026 02:46:58 PM
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
  int A, B;
  A = 10;
  B = 20;
  printf("\nBefore Swap\n");
  printf("A = %d, B = %d\n", A, B);

  A = A + B;
  B = A - B;
  A = A - B;

  printf("\nAfter Swap\n");
  printf("A = %d, B = %d\n", A, B);

  return 0;
}
