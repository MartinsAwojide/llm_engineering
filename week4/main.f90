program main
    use, intrinsic :: iso_fortran_env, only: int64
    implicit none

    integer(int64), parameter :: n = 100000
    integer(int64), parameter :: initial_seed = 42
    integer(int64), parameter :: min_v = -10
    integer(int64), parameter :: max_v = 10
    integer(int64), parameter :: a = 1664525_int64
    integer(int64), parameter :: c = 1013904223_int64

    integer(int64) :: total_sum, seed_gen, current_seed, i, k
    integer(int64), allocatable :: arr(:)
    integer(8) :: t_start, t_end, t_rate

    allocate(arr(n))
    total_sum = 0
    seed_gen = initial_seed

    call system_clock(t_start, t_rate)

    do k = 1, 20
        seed_gen = iand(a * seed_gen + c, 4294967295_int64)
        current_seed = seed_gen
        
        do i = 1, n
            current_seed = iand(a * current_seed + c, 4294967295_int64)
            arr(i) = mod(current_seed, (max_v - min_v + 1)) + min_v
        end do

        total_sum = total_sum + kadane(arr, n)
    end do

    call system_clock(t_end)

    print *, "Total Maximum Subarray Sum (20 runs):", total_sum
    print '(A, F0.6, A)', "Execution Time: ", real(t_end - t_start, 8) / real(t_rate, 8), " seconds"

contains

    function kadane(a, n) result(max_so_far)
        integer(int64), intent(in) :: n
        integer(int64), intent(in) :: a(n)
        integer(int64) :: max_so_far, max_ending_here, i

        max_so_far = -1000000000000000_int64
        max_ending_here = 0

        do i = 1, n
            max_ending_here = max_ending_here + a(i)
            if (max_so_far < max_ending_here) max_so_far = max_ending_here
            if (max_ending_here < 0) max_ending_here = 0
        end do
    end function kadane

end program main