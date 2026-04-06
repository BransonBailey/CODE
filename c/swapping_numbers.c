/*
 * =====================================================================================
 *
 *       Filename:  swapping_numbers.c
 *
 *    Description:
 *
 *        Version:  1.0
 *        Created:  04/06/2026 02:39:09 PM
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

  int temp = 0;

  printf("Before swap:\n");
  printf("A = %d\n", A);
  printf("B = %d\n", B);

  temp = A;
  A = B;
  B = temp;

  printf("After Swap:\n");
  printf("A = %d\n", A);
  printf("B = %d\n", B);

  return 0;
}
