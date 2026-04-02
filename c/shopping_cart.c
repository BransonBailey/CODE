/*
 * =====================================================================================
 *
 *       Filename:  shopping_cart.c
 *
 *    Description:  Just a simple shopping cart program.
 *                  Working with new things like fgets and floats
 *
 *        Version:  1.0
 *        Created:  04/01/2026 11:14:56 PM
 *       Revision:  none
 *       Compiler:  gcc
 *
 *      Author(s):  BransonBailey (Branson Bailey),
 *   Organization:  N/A
 *
 * =====================================================================================
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main() {
  char item[50] = "";
  float price = 0.0f;
  int quantity = 0;
  char currency = '$';
  float total = 0.0f;

  printf("What item woul you like to purchase?: ");
  fgets(item, sizeof(item), stdin);
  item[strlen(item) - 1] = '\0';

  printf("What is the price for each?: ");
  scanf("%f", &price);

  printf("How many would you like?: ");
  scanf("%d", &quantity);

  total = price * quantity;

  printf("\nYou have bought %d %s\n", quantity, item);
  printf("%c%.2f", currency, total);

  return 0;
}
