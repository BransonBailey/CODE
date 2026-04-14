/*
 * =====================================================================================
 *
 *       Filename:  vuln2.c
 *
 *    Description:  64-bit buffer overflow demonstration
 *                   Vulnerable program for 64-bit architecture
 *                   Reads input from stdin to avoid null byte issues
 *
 *        Version:  1.0
 *        Created:  04/14/2026
 *       Compiler:  gcc
 *
 *         Author:  BransonBailey (Branson Bailey),
 *   Organization:
 *
 * =====================================================================================
 */

#include <stdio.h>
#include <unistd.h>

void vulnerable_function() {
    char buffer[500];
    read(0, buffer, 1000);
}

int main() {
    vulnerable_function();
    return 0;
}
