/*
 * =====================================================================================
 *
 *       Filename:  comp_int_calc.c
 *
 *    Description:
 *
 *        Version:  1.0
 *        Created:  04/02/2026 12:33:27 PM
 *       Revision:  none
 *       Compiler:  gcc
 *
 *      Author(s):  BransonBailey (Branson Bailey),
 *   Organization:
 *
 * =====================================================================================
 */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

int main() {
  double principal = 0.0;
  double rate = 0.0;
  int years = 0;
  int timesCompounded = 0;
  double total = 0.0;

  printf("Compound Interest Calculator\n");

  printf("Enter the principal (P): ");
  scanf("%lf", &principal);

  printf("Enter the interest rate %% (r): ");
  scanf("%lf", &rate);
  rate = rate / 100;

  printf("Enter the # of years (t): ");
  scanf("%d", &years);

  printf("Enter # of times compounded per year (n): ");
  scanf("%d", &timesCompounded);

    total = principal * pow(1 + rate / timesCompounded, timesCompounded * years);
    printf("After %d years, the total will be $%.2lf", years, total);

  return 0;
}
