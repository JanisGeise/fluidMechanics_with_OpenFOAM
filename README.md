# Fluid Mechanics with OpenFOAM

Just-for-fun project to visualize some basic concepts in fluid mechanics using `OpenFOAM`, that are not part of the tutorial collection.

**Disclaimer: The test cases are intended for educational purposes rather than for validation or a quantitative assessment.
The focus is on producing qualitative animations of concepts.**

## Examples

1. `pressureWavePropagation`
   - A sinusoidal pressure source emits sound waves, which propagate through a domain
   - when imposed on a background flow field, a Mach cone starts to form when the speed of sound is reached
   - goal is to visualize the formation of shocks and how disturbances travel in the flow field
   - TODO: ramp up `U` during a single simulation instead of having a const. inlet velocity without messing up the acoustics

   <table>
     <tr>
       <td>
         <video src="https://github.com/user-attachments/assets/7a45dbb1-40b8-4d08-9505-5a9fc9953be0" controls muted loop width="100%"></video>
       </td>
       <td>
         <video src="https://github.com/user-attachments/assets/a6e129a7-e2b8-47d8-991f-6aa2b7d6e69d" controls muted loop width="100%"></video>
       </td>
       <td>
         <video src="https://github.com/user-attachments/assets/1505139a-a879-479d-82cc-200ec16d8308" controls muted loop width="100%"></video>
       </td>
     </tr>
   </table>

The animations show the propagation of acoustic waves for $Ma_\infty = 0$ (left), $Ma_\infty = 0.5$ (middle) and
$Ma_\infty = 1.25$ (right).

## Ideas for other test cases

1. A Laval nozzle to demonstrate under- and overexpansion

## Installation of the dependencies

still TODO

## Running a case

To run a case, execute the `Allrun` located in the corresponding case directory.
To reset a simulation, execute the `Allclean`.
Further information can be found in the `Readme.md` files in each case setup.

## Contributing

If you have any ideas for new setups or suggestions for improvements, feel free to open up an issue.

## License

This work is [GPLv3](https://en.wikipedia.org/wiki/GNU_General_Public_License)-licensed, for more information it is referred to the [LICENSE](LICENSE) file.
