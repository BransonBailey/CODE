/*
 * =====================================================================================
 *
 *       Filename:  vuln.c
 *
 *    Description:
 *
 *        Version:  1.0
 *        Created:  04/14/2026 02:18:49 PM
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
#include <string.h>

int main(int argc, char **argv) {
  char buffer[500];
  strcpy(buffer, argv[1]);

  return 0;
}
